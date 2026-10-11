"""Native fullscreen suite with a narrowly scoped web-to-native bridge."""
import json,os,sys
from pathlib import Path
from urllib.parse import urlsplit
from PySide6.QtCore import QObject,Signal,Slot,QTimer,QUrl,Qt
from PySide6.QtGui import QDesktopServices,QIcon
from PySide6.QtWidgets import QApplication,QMainWindow,QMessageBox
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage,QWebEngineProfile,QWebEngineSettings,QWebEngineUrlRequestInterceptor
from PySide6.QtWebChannel import QWebChannel
from core import VERSION,resource
from gateway import Gateway
import threading,time
from scene_server import SceneServer
class LocalRequests(QWebEngineUrlRequestInterceptor):
 def __init__(self,origin,parent=None):super().__init__(parent);self.origin=origin
 def interceptRequest(self,info):
  u=info.requestUrl();parsed=urlsplit(u.toString())
  allowed=u.scheme() in ("qrc","data","blob","about") or (u.scheme()=="http" and parsed.netloc==self.origin)
  if not allowed:info.block(True)
class ScenePage(QWebEnginePage):
 def __init__(self,profile,origin,parent=None):super().__init__(profile,parent);self.origin=origin
 def acceptNavigationRequest(self,url,kind,is_main):
  if not is_main:return True
  return url.scheme()=="about" or (url.scheme()=="http" and urlsplit(url.toString()).netloc==self.origin)
class SceneBridge(QObject):
 stateChanged=Signal(str);sceneAction=Signal(str)
 def __init__(self,backend,window):
  super().__init__(window);self.backend=backend;self.window=window;self.scene_ready=False
  backend.changed.connect(self.publish);backend.messagesChanged.connect(self.publish);backend.activityChanged.connect(self.publish);backend.updateChanged.connect(self.publish);backend.sceneAction.connect(self.sceneAction)
 @Slot(result=str)
 def snapshot(self):
  b=self.backend
  return json.dumps({"version":VERSION,"reply":b.lastReply,"status":b.status,"busy":b.busy,"recording":b.recording,"talking":b.talking,"conversation":b.conversation,"speechLevel":b.audioLevel,"mood":b.moodId,"updateProgress":b.updateProgress,"updateNote":b.updateNote,"updateState":b.updateState},ensure_ascii=False)
 def publish(self):self.stateChanged.emit(self.snapshot())
 @Slot()
 def login(self):
  if getattr(self,"pairing",False):return
  self.pairing=True;self.backend.set_status("Opening private Google sign-in…")
  def done(result):
   if isinstance(result,Exception):self.pairing=False;self.backend.set_status(str(result));return
   self.backend.set_status("Link code: "+result["user_code"]+" · enter this in your private console")
   QDesktopServices.openUrl(QUrl(result["login_url"]))
   def poll():
    while time.time()<result["expires_at"] and not self.backend.closed:
     if self.backend.gateway.poll(result):return self.backend.gateway.migrate(self.backend.keys,self.backend.store.settings)
     time.sleep(2)
    raise RuntimeError("Google linking expired. Choose sign in again.")
   def linked(value):
    self.pairing=False
    self.backend.set_status(str(value) if isinstance(value,Exception) else "Google connected · private controls are ready")
    self.backend.refresh();self.publish()
   self.backend.work(poll,linked)
  self.backend.work(self.backend.gateway.start,done)
 @Slot()
 def logout(self):
  self.backend.stop();self.backend.gateway.logout();self.backend.refresh();self.backend.set_status("Desktop signed out")
 @Slot()
 def memories(self):self.backend.memory()
 @Slot()
 def studio(self):self.backend.studio()
 @Slot()
 def ready(self):self.scene_ready=True;self.backend.scene_enabled=True;self.publish();self.window.scene_loaded()
 @Slot(str)
 def send(self,text):
  if isinstance(text,str) and len(text)<=4000:self.backend.send(text)
 @Slot()
 def toggleVoice(self):self.backend.toggleConversation()
 @Slot()
 def interrupt(self):self.backend.stop();self.sceneAction.emit("stop")
 @Slot()
 def bargeIn(self):
  active=self.backend.conversation;self.backend.cancel_turn()
  if active:self.backend.listen_again()
 @Slot()
 def checkUpdate(self):self.backend.checkUpdate()
 @Slot()
 def openControlCenter(self):
  cfg=resource("control-center.json")
  try:url=json.loads(cfg.read_text(encoding="utf8")).get("url","")
  except (OSError,ValueError):url=""
  p=urlsplit(url)
  if p.scheme=="https" and p.hostname and not p.username and not p.password:QDesktopServices.openUrl(QUrl(url))
  else:QMessageBox.information(self.window,"Lisa · Control center","The private control center has not been connected yet. Your existing local settings are preserved.")
 @Slot()
 def localRecoverySettings(self):self.backend.settings()
 @Slot()
 def toggleFullscreen(self):
  if self.window.isFullScreen():self.window.showNormal()
  else:self.window.showFullScreen()
 @Slot()
 def quit(self):self.backend.app.quit()
class SuiteWindow(QMainWindow):
 def __init__(self,backend,server,test=False):
  super().__init__();self.backend=backend;self.server=server;self.test=test;self.acknowledged=False;self.setWindowTitle("LISA · Kitty Corp");self.resize(1440,900)
  self.profile=QWebEngineProfile(self)
  self.view=QWebEngineView(self);self.setCentralWidget(self.view)
  origin=urlsplit(server.url).netloc;self.page=ScenePage(self.profile,origin,self.view);self.view.setPage(self.page)
  self.interceptor=LocalRequests(origin,self.profile);self.profile.setUrlRequestInterceptor(self.interceptor)
  self.page.settings().setAttribute(QWebEngineSettings.WebGLEnabled,True)
  self.page.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls,False)
  self.page.featurePermissionRequested.connect(lambda origin,feature:self.page.setFeaturePermission(origin,feature,QWebEnginePage.PermissionDeniedByUser))
  self.channel=QWebChannel(self.page);self.bridge=SceneBridge(backend,self);self.channel.registerObject("companion",self.bridge);self.page.setWebChannel(self.channel)
  self.view.setUrl(QUrl(server.url));self.page.renderProcessTerminated.connect(self.render_failed)
  self.guard=QTimer(self);self.guard.setSingleShot(True);self.guard.timeout.connect(lambda:backend.set_status("The room is taking longer to load. Restart Lisa or use local recovery settings."));self.guard.start(45000)
 def render_failed(self,*_):self.backend.stop();QMessageBox.warning(self,"Lisa · Graphics","The room renderer stopped. Restart Lisa. Your settings and memories are preserved.")
 def scene_loaded(self):
  self.guard.stop()
  if self.acknowledged:return
  self.acknowledged=True
  if self.test:
   QTimer.singleShot(1800,self.capture_test);return
  QTimer.singleShot(700,self.backend.recover_update_status)
  ack=os.environ.pop("LISA_UPDATE_ACK","");expected=os.environ.pop("LISA_UPDATE_VERSION","")
  if ack and expected==VERSION:
   path=Path(ack).resolve()
   if path.parent==(self.backend.store.directory/"updates").resolve() and path.name.startswith("launched-"):
    from updater_worker import write_json
    write_json(path,{"version":VERSION,"pid":os.getpid(),"ui_loaded":True,"scene_loaded":True})
 def capture_test(self):
  self.view.grab().save(str(self.backend.store.directory/"ui-self-test.png"));self.backend.close()
  (self.backend.store.directory/"self-test.json").write_text(json.dumps({"version":VERSION,"ui_loaded":True,"scene_loaded":True,"microphone_closed":self.backend.audio.input_stream is None,"output_closed":self.backend.audio.output_stream is None,"native_bridge":True}))
  self.backend.app.quit()
 def closeEvent(self,event):self.backend.close();event.accept()
def main(Backend):
 QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
 app=QApplication(sys.argv);app.setApplicationName("LISA");app.setOrganizationName("Kitty Corp");app.setWindowIcon(QIcon(str(resource("assets/lisa.ico"))))
 backend=Backend(app);backend.gateway=Gateway(backend.store.directory);server=SceneServer(resource("assets/suite"));test="--self-test" in sys.argv
 window=SuiteWindow(backend,server,test);backend.window=window;app.aboutToQuit.connect(backend.close)
 if test:window.showNormal()
 elif backend.store.settings["fullscreen"]:window.showFullScreen()
 else:window.show()
 code=app.exec();backend.close();server.close();window.view.setPage(QWebEnginePage(window.view));window.page.deleteLater();return code
