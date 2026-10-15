"""Godot Standard frontend; Python owns keys, audio, reviewed tools and updates."""
from __future__ import annotations
import json,os,secrets,sys,threading,time,subprocess
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from PySide6.QtCore import QObject,Signal,QTimer
from PySide6.QtGui import QIcon,QDesktopServices
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtCore import QUrl
from core import resource,VERSION
from gateway import Gateway

COMMANDS=frozenset(("ready","enter","send","voice","interrupt","quit","settings","memory","update","shortcut","console","login","logout","follow","motion","barge","routines","affection","effects","outfit","buy"))
class EngineBridge(QObject):
    requested=Signal(str,object)
    def __init__(self,backend):
        super().__init__();self.backend=backend;self.entered=False;self.ready=False;self.lock=threading.RLock();self.events=[];self.seq=0;self.state={};self.pairing=False
        self.requested.connect(self.dispatch);backend.sceneAction.connect(self.scene_action)
        self.timer=QTimer(self);self.timer.timeout.connect(self.publish);self.timer.start(80);self.publish()
    def scene_action(self,action):
        with self.lock:
            self.seq+=1;self.events.append({"id":self.seq,"action":action});self.events=self.events[-80:]
    def publish(self):
        b=self.backend
        with self.lock:self.state={"version":VERSION,"reply":b.lastReply,"status":b.status,"busy":b.busy,"recording":b.recording,"talking":b.talking,"conversation":b.conversation,"speechLevel":b.audioLevel,"mood":b.moodId,"updateProgress":b.updateProgress,"updateNote":b.updateNote,"updateState":b.updateState,"follow":bool(b.store.settings.get("camera_follow",True)),"motion":bool(b.store.settings.get("motion",True)),"routines":bool(b.store.settings.get("routines",True)),"affection":bool(b.store.settings.get("affection",False)),"effects":bool(b.store.settings.get("effects",True)),"outfit":int(b.store.settings.get("illustrated_outfit",0))}
    def snapshot(self,since=0):
        with self.lock:return {**self.state,"events":[e for e in self.events if e["id"]>since]}
    def acknowledge(self,activation_required=False):
        ack=os.environ.pop("LISA_UPDATE_ACK","");expected=os.environ.pop("LISA_UPDATE_VERSION","")
        if ack and expected==VERSION:
            path=Path(ack).resolve()
            if path.parent==(self.backend.store.directory/"updates").resolve() and path.name.startswith("launched-"):
                from updater_worker import write_json
                write_json(path,{"version":VERSION,"pid":os.getpid(),"ui_loaded":True,"scene_loaded":not activation_required,"title_ready":True,"activation_required":activation_required,"engine":"Activation screen" if activation_required else "Godot Standard"})
    def dispatch(self,name,value):
        b=self.backend
        if name=="ready":
            if not self.ready:self.ready=True;self.acknowledge();QTimer.singleShot(700,b.recover_update_status)
        elif name=="enter":self.entered=True;b.scene_enabled=True
        elif name=="send" and self.entered:b.send(str(value)[:4000])
        elif name=="voice" and self.entered:b.toggleConversation()
        elif name=="barge" and self.entered:
            active=b.conversation;b.cancel_turn()
            if active:b.listen_again()
        elif name=="interrupt":b.stop();self.scene_action("stop")
        elif name=="quit":b.app.quit()
        elif name=="settings":b.settings()
        elif name=="memory":b.memory()
        elif name=="update":b.checkUpdate()
        elif name=="shortcut":b.createDesktopShortcut()
        elif name=="console":QDesktopServices.openUrl(QUrl(b.gateway.url))
        elif name=="logout":b.stop();b.gateway.logout();b.refresh()
        elif name=="login":self.login()
        elif name=="buy":QDesktopServices.openUrl(QUrl("https://kittycorp.vercel.app/"))
        elif name=="outfit":
            b.store.settings["illustrated_outfit"]=value;b.store.save();b.refresh()
        elif name in ("routines","affection","effects"):
            b.store.settings[name]=value;b.store.save();b.refresh()
        elif name in ("follow","motion"):
            b.store.settings["camera_follow" if name=="follow" else "motion"]=bool(value);b.store.save();b.refresh()
        self.publish()
    def login(self):
        if self.pairing:return
        self.pairing=True
        def started(result):
            if isinstance(result,Exception):self.pairing=False;self.backend.set_status(str(result));return
            self.backend.set_status("Link code: "+result["user_code"]+" · enter this in your private console");QDesktopServices.openUrl(QUrl(result["login_url"]))
            def poll():
                while time.time()<result["expires_at"] and not self.backend.closed:
                    if self.backend.gateway.poll(result):return self.backend.gateway.migrate(self.backend.keys,self.backend.store.settings)
                    time.sleep(2)
                raise RuntimeError("Google linking expired. Choose sign in again.")
            def done(value):self.pairing=False;self.backend.set_status(str(value) if isinstance(value,Exception) else "Google connected · private controls ready");self.backend.refresh()
            self.backend.work(poll,done)
        self.backend.work(self.backend.gateway.start,started)

class EngineServer:
    def __init__(self,bridge):
        self.token=secrets.token_urlsafe(48);token=self.token
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def respond(self,code,data):
                raw=json.dumps(data,ensure_ascii=False).encode();self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(raw)));self.send_header("Cache-Control","no-store");self.end_headers()
                try:self.wfile.write(raw)
                except (BrokenPipeError,ConnectionResetError):pass
            def authorized(self):
                expected="127.0.0.1:"+str(self.server.server_port)
                return self.headers.get("Host")==expected and not self.headers.get("Origin") and secrets.compare_digest(self.headers.get("Authorization",""),"Bearer "+token)
            def do_GET(self):
                if not self.authorized():return self.respond(403,{"error":"Forbidden"})
                from urllib.parse import urlsplit,parse_qs
                p=urlsplit(self.path)
                if p.path!="/state":return self.respond(404,{"error":"Not found"})
                try:since=max(0,int(parse_qs(p.query).get("since",["0"])[0]))
                except ValueError:return self.respond(400,{"error":"Invalid cursor"})
                self.respond(200,bridge.snapshot(since))
            def do_POST(self):
                if not self.authorized():return self.respond(403,{"error":"Forbidden"})
                if self.path!="/command":return self.respond(404,{"error":"Not found"})
                try:
                    length=int(self.headers.get("Content-Length","0"))
                    if not 0<length<=18000:raise ValueError()
                    data=json.loads(self.rfile.read(length));name=data["name"];value=data.get("value")
                    if name not in COMMANDS:raise ValueError()
                    if name=="send" and (not isinstance(value,str) or len(value)>4000):raise ValueError()
                    if name in ("follow","motion","routines","affection","effects") and not isinstance(value,bool):raise ValueError()
                    if name=="outfit" and (type(value) is not int or value not in (0,1)):raise ValueError()
                    if name not in ("send","follow","motion","routines","affection","effects","outfit") and value is not None:raise ValueError()
                except (ValueError,KeyError,TypeError):return self.respond(400,{"error":"Invalid command"})
                bridge.requested.emit(name,value);self.respond(202,{"accepted":True})
        self.http=ThreadingHTTPServer(("127.0.0.1",0),Handler);self.http.daemon_threads=True
        self.url="http://127.0.0.1:"+str(self.http.server_port)
        threading.Thread(target=self.http.serve_forever,daemon=True).start()
    def close(self):self.http.shutdown();self.http.server_close()

def main(Backend):
    app=QApplication(sys.argv);app.setQuitOnLastWindowClosed(False);app.setApplicationName("LISA");app.setOrganizationName("Kitty Corp");app.setWindowIcon(QIcon(str(resource("assets/lisa.ico"))))
    backend=Backend(app);backend.gateway=Gateway(backend.store.directory);backend.scene_enabled=False
    from activation_ui import require_activation
    bridge=EngineBridge(backend)
    if not require_activation(backend,lambda:bridge.acknowledge(True)):
        bridge.timer.stop();backend.close();return 3
    server=EngineServer(bridge);engine=None
    test="--self-test" in sys.argv
    try:
        env=os.environ.copy();env.update(LISA_ENGINE_URL=server.url,LISA_ENGINE_TOKEN=server.token,LISA_ENGINE_DATA=str(backend.store.directory))
        if test:env["LISA_ENGINE_TEST"]="1"
        if getattr(sys,"frozen",False):
            executable=Path(sys.executable).resolve().parent/"engine/LISA-Engine.exe";args=[str(executable)]
        else:
            executable=Path(os.environ.get("LISA_GODOT",""))
            if not executable.is_file():raise RuntimeError("Godot Standard is missing. Set LISA_GODOT to the official engine executable.")
            args=[str(executable),"--path",str(resource("godot"))]
        if test:args+=["--","--self-test"]
        # Engine receives a random, per-launch loopback token. Never provider keys.
        engine=subprocess.Popen(args,env=env,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        guard=QTimer();guard.timeout.connect(lambda:app.quit() if engine.poll() is not None else None);guard.start(500)
        def fail():
            if not bridge.ready:
                QMessageBox.warning(None,"Lisa · Room could not start","The native room could not load. Your settings and memories are preserved. Reinstall the latest Lisa or check your graphics driver.");app.quit()
        startup=QTimer();startup.setSingleShot(True);startup.timeout.connect(fail);startup.start(90000)
        app.aboutToQuit.connect(backend.close)
        code=app.exec()
        if test:
            path=backend.store.directory/"self-test.json"
            try:data=json.loads(path.read_text()) if path.exists() else {}
            except (ValueError,OSError):data={"engine_report_incomplete":True}
            data.update(version=VERSION,ui_loaded=bridge.ready,session_entered=bridge.entered,microphone_closed=backend.audio.input_stream is None,output_closed=backend.audio.output_stream is None,native_bridge=True)
            path.write_text(json.dumps(data,indent=2))
        return code
    except (OSError,RuntimeError) as exc:QMessageBox.warning(None,"Lisa · Engine",str(exc));return 2
    finally:
        backend.close();server.close()
        if engine and engine.poll() is None:
            engine.terminate()
            try:engine.wait(timeout=8)
            except subprocess.TimeoutExpired:engine.kill();engine.wait()
