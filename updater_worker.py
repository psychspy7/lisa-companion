"""Independent Windows updater. Runs outside the app being replaced; no Qt or shell."""
from __future__ import annotations
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


def write_json(path, record):
    path=Path(path)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(record),encoding='utf-8')
    temporary.replace(path)


def file_hash(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


class Parent:
    def __init__(self,pid):
        self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        self.kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
        self.kernel.OpenProcess.restype=wintypes.HANDLE
        self.kernel.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
        self.kernel.WaitForSingleObject.restype=wintypes.DWORD
        self.kernel.CloseHandle.argtypes=[wintypes.HANDLE]
        self.handle=self.kernel.OpenProcess(0x00100000,False,pid)
        if not self.handle and ctypes.get_last_error()!=87:
            raise OSError('Windows could not monitor Lisa closing. Keep Lisa open and retry.')
    def wait(self,seconds):
        return not self.handle or self.kernel.WaitForSingleObject(self.handle,int(seconds*1000))==0
    def close(self):
        if self.handle:self.kernel.CloseHandle(self.handle);self.handle=None


def close_other_windows(target):
    """Request a normal close only from windows owned by this exact Lisa executable."""
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    user=ctypes.WinDLL('user32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    user.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
    user.PostMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
    callback_type=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    @callback_type
    def visit(window,param):
        pid=wintypes.DWORD()
        user.GetWindowThreadProcessId(window,ctypes.byref(pid))
        handle=kernel.OpenProcess(0x1000,False,pid.value)
        if handle:
            try:
                size=wintypes.DWORD(32768);name=ctypes.create_unicode_buffer(size.value)
                if kernel.QueryFullProcessImageNameW(handle,0,name,ctypes.byref(size)) and Path(name.value).resolve()==target:
                    user.PostMessageW(window,0x0010,0,0) # WM_CLOSE: lets Lisa save and release the mic.
            finally:kernel.CloseHandle(handle)
        return True
    user.EnumWindows.argtypes=[callback_type,wintypes.LPARAM]
    user.EnumWindows(visit,0)


def launch(command,**kwargs):
    env=dict(os.environ,PYINSTALLER_RESET_ENVIRONMENT='1')
    # External processes must use Windows' DLL search path, not our extracted runtime.
    if os.name=='nt':ctypes.windll.kernel32.SetDllDirectoryW(None)
    return subprocess.Popen(command,env=kwargs.pop('env',env),
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)|getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0),**kwargs)


def run_job(manifest):
    job=json.loads(Path(manifest).read_text(encoding='utf-8'))
    directory=Path(job['directory']).resolve()
    target=Path(job['target']).resolve();source=Path(job['source']).resolve()
    job_id=job['id'];version=job['version'].lstrip('v')
    if not re.fullmatch(r'[0-9a-f]{32}',job_id) or not re.fullmatch(r'\d+\.\d+\.\d+',version):
        raise ValueError('Invalid update job.')
    if source.parent!=directory/'updates' or target.suffix.lower()!='.exe' or job['kind'] not in ('installer','portable'):
        raise ValueError('Invalid update location.')
    status_path=directory/'update-result.json'
    def status(state,message):
        write_json(status_path,{'status':state,'message':message,'version':version,'job_id':job_id,'updater_pid':os.getpid()})
    parent=None;replaced=False;backup=target.with_name(target.name+'.bak');new_app=None;setup=None
    try:
        if source.stat().st_size!=job['size'] or file_hash(source)!=job['sha256']:
            raise RuntimeError('The downloaded update changed. Download it again.')
        parent=Parent(job['parent_pid'])
        status('waiting','Closing Lisa before installing…')
        write_json(directory/'updates'/('ready-'+job_id+'.json'),{'id':job_id,'ready':True})
        if not parent.wait(120):
            raise RuntimeError('Lisa could not finish closing. Close Lisa and retry the update.')
        close_other_windows(target)
        status('installing','Installing Lisa '+version+'…')
        if job['kind']=='installer':
            log=directory/'updates'/('setup-'+job_id+'.log')
            setup=launch([str(source),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS','/UPDATE','/DIR='+str(target.parent),'/LOG='+str(log)],cwd=directory/'updates')
            code=setup.wait(timeout=600)
            if code!=0:raise RuntimeError(f'Lisa Setup could not finish (exit {code}). Close other Lisa windows and retry, or run the latest Setup.')
            marker=json.loads((target.parent/'install-state.json').read_text(encoding='utf-8-sig'))
            installed=json.loads((target.parent/'_internal/version.json').read_text(encoding='utf-8-sig'))
            if marker.get('application')!='LISA' or marker.get('version')!=version or installed.get('version')!=version:
                raise RuntimeError('Setup did not install the expected Lisa version. Run the latest Setup.')
        else:
            stage=target.with_name(target.name+'.new')
            shutil.copyfile(source,stage)
            if file_hash(stage)!=job['sha256']:raise RuntimeError('The staged update failed its checksum.')
            for attempt in range(120):
                try:
                    shutil.copyfile(target,backup)
                    os.replace(stage,target);replaced=True;break
                except OSError:
                    if attempt==119:raise
                    time.sleep(.5)
            if file_hash(target)!=job['sha256']:raise RuntimeError('The installed update failed its checksum.')
        status('restarting','Opening the updated Lisa…')
        ack=directory/'updates'/('launched-'+job_id+'.json')
        env=dict(os.environ,PYINSTALLER_RESET_ENVIRONMENT='1',LISA_DATA_DIR=str(directory),
            LISA_UPDATE_ACK=str(ack),LISA_UPDATE_VERSION=version)
        new_app=launch([str(target)],cwd=target.parent,env=env)
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            if ack.exists():
                if json.loads(ack.read_text()).get('version')==version:
                    status('success','Lisa '+version+' was installed and restarted successfully.')
                    return 0
                raise RuntimeError('The restarted Lisa has the wrong version. Run the latest Setup.')
            if new_app.poll() is not None:raise RuntimeError('The updated Lisa could not start. Run the latest Setup.')
            time.sleep(.2)
        raise RuntimeError('Lisa did not confirm its restart. Open Lisa again; the installation is saved.')
    except Exception as exc:
        message='Update failed: '+str(exc)
        if replaced and backup.is_file() and (new_app is None or new_app.poll() is not None):
            try:os.replace(backup,target)
            except OSError:message+=' Run the latest Setup to restore Lisa.'
        status('failed',message)
        # Never open a duplicate when the old or newly launched Lisa is still running.
        if parent and parent.wait(0) and (setup is None or setup.poll() is not None) and (new_app is None or new_app.poll() is not None) and target.is_file():
            try:launch([str(target)],cwd=target.parent,env=dict(os.environ,PYINSTALLER_RESET_ENVIRONMENT='1',LISA_DATA_DIR=str(directory)))
            except OSError:pass
        return 1
    finally:
        if parent:parent.close()


if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit(2)
    raise SystemExit(run_job(sys.argv[1]))
