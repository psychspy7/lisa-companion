"""Reproducible Standard-engine Windows export, native backend and Inno installer."""
from pathlib import Path
import argparse,subprocess,sys,os,shutil,json,zipfile
def build(godot,templates,output,compiler=None):
    source=Path(__file__).resolve().parents[1];godot=Path(godot).resolve();templates=Path(templates).resolve();output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    if not godot.is_file():raise RuntimeError("Choose the Godot Standard executable.")
    release=templates/"windows_release_x86_64.exe"
    if not release.is_file():raise RuntimeError("Extract matching Standard export templates; windows_release_x86_64.exe is required.")
    template_version=templates/"version.txt"
    if not template_version.is_file() or not template_version.read_text().strip().startswith("4.7.2.stable"):
        raise RuntimeError("Templates must match Godot 4.7.2 Standard.")
    version=subprocess.check_output([str(godot),"--headless","--version"],text=True).strip()
    if version!="4.7.2.stable.official.ed1daf0bf":raise RuntimeError("This release is verified with Godot 4.7.2 Standard. Use matching engine and templates.")
    env=os.environ.copy()
    env["PATH"]=";".join(v for v in env.get("PATH","").split(";") if "/dependencies/native/" not in v.replace("\\","/").lower())
    def run(args):subprocess.run(args,cwd=source,env=env,check=True)
    run([str(godot),"--headless","--editor","--path",str(source/"godot"),"--import","--quit"])
    preset=source/"godot/export_presets.cfg";original=preset.read_text()
    exported=output/"LISA-Engine.exe"
    try:
        preset.write_text(original.replace('custom_template/release=""','custom_template/release="'+release.as_posix()+'"'))
        run([str(godot),"--headless","--path",str(source/"godot"),"--export-release","Windows Desktop",str(exported)])
    finally:preset.write_text(original)
    run([sys.executable,"-m","PyInstaller","--noconfirm","--clean","--distpath",str(output),"lisa-updater.spec"])
    env["LISA_UPDATER_EXE"]=str(output/"LISA-Updater.exe")
    run([sys.executable,"-m","PyInstaller","--noconfirm","--clean","--distpath",str(output),"lisa-installed.spec"])
    app=output/"LISA-App";(app/"engine").mkdir(exist_ok=True);shutil.copy2(exported,app/"engine/LISA-Engine.exe")
    (app/"licenses").mkdir(exist_ok=True)
    for name in ("GODOT-LICENSE.txt","GODOT-COPYRIGHT.txt"):shutil.copy2(source/"licenses"/name,app/"licenses"/name)
    args=[sys.executable,"installer/build_setup.py",str(output)]
    if compiler:args+=["--compiler",str(compiler)]
    run(args)
    with zipfile.ZipFile(output/"LISA-Portable.zip","w",compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for p in app.rglob("*"):
            if p.is_file():z.write(p,Path("LISA")/p.relative_to(app))
    print("Built",output/"LISA-Setup.exe")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--godot",required=True);p.add_argument("--templates",required=True);p.add_argument("--output",default="dist");p.add_argument("--compiler")
    a=p.parse_args();build(a.godot,a.templates,a.output,a.compiler)
