"""Qt Quick desktop shell, interruptible provider work and reviewed native tools."""
from datetime import datetime
import json
from pathlib import Path
import sys
import threading
import time
from PySide6.QtCore import QObject,Property,Signal,Slot,QTimer,QUrl,Qt
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import QApplication,QMessageBox,QFileDialog,QDialog,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QPushButton,QListWidget,QLineEdit
from core import Store,Credentials,MOODS,OUTFITS,LABELS,VERSION,ApiError,resource,outfit_for_hour
from providers import GroqClient,GeminiClient,ElevenLabsClient,FishClient
from audio import Audio
from actions import validate_action,explicit_local_action,open_target
from motion import MotionCache,ViduClient
from settings_ui import SettingsDialog,STYLE
import demo
import updates


class Backend(QObject):
    changed=Signal(); messagesChanged=Signal(); imageChanged=Signal(str); clipChanged=Signal(str); completed=Signal(object,object)
    activityChanged=Signal(); updateChanged=Signal(); downloadProgress=Signal(int,int)
    def __init__(self,app):
        super().__init__();self.app=app;self.store=Store();self.audio=Audio()
        self.keys={p:Credentials(self.store.directory,p) for p in ("groq","gemini","elevenlabs","fish","vidu")}
        self.cache=MotionCache(self.store.directory);self.jobs=self.store.load("motion-jobs.json",[])
        self.mood="smile";self.outfit=outfit_for_hour(datetime.now().hour) if self.store.settings["auto_outfit"] else self.store.settings["outfit"]
        self._status="Ready, Sir";self._busy=False;self.closed=False;self.generation=0;self.cancel_event=threading.Event();self.speaking=False
        self._messages=list(self.store.history[-60:]);self.window=None;self.polling=False;self.started_recording=0
        self._mode_name="Offline preview";self._last_audio=None;self._updating=False;self._update_progress=-1;self._update_note="";self._update_state="idle"
        self.completed.connect(self.dispatch)
        self.downloadProgress.connect(self.on_update_progress)
        self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(100)
        self.motion_timer=QTimer(self);self.motion_timer.timeout.connect(self.poll_job);self.motion_timer.start(10000)
        if not self._messages:self.add_message("assistant","Missed me, Sir? Make yourself comfortable.")
        self.refresh()

    @Property(str,notify=changed)
    def status(self):return self._status
    @Property(bool,notify=changed)
    def busy(self):return self._busy
    @Property(bool,notify=activityChanged)
    def recording(self):return self.audio.recording
    @Property(bool,notify=activityChanged)
    def talking(self):return self.speaking or self.audio.playing
    @Property(float,notify=activityChanged)
    def audioLevel(self):return self.audio.level
    @Property(str,notify=changed)
    def outfitName(self):return self.outfit.title()
    @Property(str,notify=changed)
    def moodName(self):return LABELS[self.mood]
    @Property(str,notify=changed)
    def modeName(self):return self._mode_name
    @Property(str,constant=True)
    def version(self):return VERSION
    @Property(bool,notify=updateChanged)
    def updateInProgress(self):return self._updating
    @Property(float,notify=updateChanged)
    def updateProgress(self):return self._update_progress
    @Property(str,notify=updateChanged)
    def updateNote(self):return self._update_note
    @Property(str,notify=updateChanged)
    def updateState(self):return self._update_state
    @Property(str,notify=changed)
    def portrait(self):return self.image_url()
    @Property(bool,notify=changed)
    def motionEnabled(self):return self.store.settings["motion"]
    @Property(float,notify=changed)
    def initialZoom(self):return float(self.store.settings.get("zoom",1))
    @Property(int,notify=changed)
    def chatWidth(self):return int(self.store.settings.get("chat_width",390))
    @Property("QVariantList",notify=messagesChanged)
    def messages(self):return self._messages
    @Property("QVariantList",constant=True)
    def moods(self):return [{"id":m,"label":LABELS[m]} for m in MOODS]

    def image_path(self):
        path=resource("assets/portraits/"+self.outfit+".webp") if self.mood=="smile" else resource("assets/poses/"+self.mood+".webp")
        if not path.exists():path=resource("assets/portraits/"+self.outfit+".png")
        return path
    def image_url(self):return QUrl.fromLocalFile(str(self.image_path())).toString()
    def refresh(self):
        self.motion_timer.start(10000)
        provider=self.store.settings["chat_provider"]
        self._mode_name=provider.title() if self.keys.get(provider) and self.keys[provider].get() else "Offline preview"
        if self.store.settings["auto_outfit"] and self.mood=="smile":self.outfit=outfit_for_hour(datetime.now().hour)
        self.changed.emit();self.imageChanged.emit(self.image_url())
    def set_status(self,value):self._status=value;self.changed.emit();self.activityChanged.emit()
    def add_message(self,role,text):
        self._messages.append({"role":role,"content":text});self._messages=self._messages[-80:];self.messagesChanged.emit()
        self.store.history=list(self._messages);self.store.save()

    def client(self,provider):
        classes={"groq":GroqClient,"gemini":GeminiClient,"elevenlabs":ElevenLabsClient,"fish":FishClient,"vidu":ViduClient}
        if provider not in classes:raise ApiError("Choose a supported service in Settings.")
        return classes[provider](self.keys[provider].get(),self.store.settings)

    def work(self,fn,callback):
        def run():
            try:result=fn()
            except (ApiError,ValueError) as exc:result=exc
            except Exception:result=RuntimeError("This operation could not finish. Check your settings and connection, then try again.")
            if not self.closed:self.completed.emit(callback,result)
        threading.Thread(target=run,daemon=True).start()
    @Slot(object,object)
    def dispatch(self,callback,result):
        if not self.closed:callback(result)

    @Slot(str)
    def send(self,text):
        text=text.strip()[:4000]
        if not text or self._busy:return
        self.stop();history=[x for x in self._messages if x["role"] in ("user","assistant")]
        self.add_message("user",text);self._busy=True;self.set_status("Thinking…");token=self.generation
        local=explicit_local_action(text)
        if local:
            self.finish_reply({"reply":"Let’s open "+local["value"]+", Sir.","mood":"listening","action":local},token);return
        if any(x in text.casefold() for x in ("who made you","who created you","who maded you")):
            self.finish_reply({"reply":"I am made by Virat by the help of Kitty Corp organisation.","mood":"proud"},token);return
        provider=self.store.settings["chat_provider"]
        key=self.keys.get(provider)
        if not key or not key.get():
            if self.store.settings["demo_enabled"]:self.finish_reply(demo.reply(text,self.store.memories),token)
            else:self.finish_reply(ApiError("Add your chat API key in Settings, or enable the offline preview."),token)
            return
        client=self.client(provider);memories=list(self.store.memories)
        self.work(lambda:client.chat(text,history,memories),lambda result:self.finish_reply(result,token))

    def finish_reply(self,result,token):
        if token!=self.generation:return
        self._busy=False
        if isinstance(result,Exception):self.set_status(str(result));return
        self.setMood(result["mood"]);self.add_message("assistant",result["reply"]);self.set_status("Ready, Sir")
        action=result.get("action")
        if action:self.review_action(action)
        if self.store.settings["voice_enabled"]:self.speak(result["reply"],result["mood"],token)

    def review_action(self,action):
        kind,value=action.get("type"),action.get("value","")
        if kind=="set_mood" and value in MOODS:self.setMood(value);return
        if kind=="set_outfit" and value in OUTFITS:self.setOutfit(value);return
        if not self.store.settings["pc_actions"]:self.add_message("system","PC actions are turned off in Settings.");return
        try:kind,value=validate_action(action)
        except ValueError as exc:self.add_message("system",str(exc));return
        labels={"open_app":"Open app","open_url":"Open website","copy_text":"Copy to clipboard","create_note":"Save a text note"}
        if QMessageBox.question(None,"Lisa · Review PC action",labels[kind]+"\n\n"+value[:1600],QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:
            self.add_message("system","Action cancelled.");return
        try:
            if kind=="copy_text":self.app.clipboard().setText(value)
            elif kind=="create_note":
                path,_=QFileDialog.getSaveFileName(None,"Save Lisa's note","Lisa-note.txt","Text files (*.txt)")
                if not path:self.add_message("system","Note not saved.");return
                if Path(path).suffix.lower()!=".txt":raise ValueError("Choose a .txt file.")
                Path(path).write_text(value,encoding="utf-8")
            else:open_target(kind,value)
            self.add_message("system",labels[kind]+" completed.")
        except Exception:self.add_message("system","Windows could not complete that action.")

    def speak(self,text,mood,token):
        primary=self.store.settings["voice_provider"];cancel=self.cancel_event
        self.speaking=True;self.set_status("Preparing voice…")
        def generate():
            if primary=="windows":return demo.speech(text,self.store.directory,cancel),"Windows voice"
            try:return self.client(primary).speech(text,mood),primary.title()
            except ApiError:
                if primary=="elevenlabs" and self.store.settings["voice_fallback"] and self.keys["fish"].get() and self.store.settings["fish_voice_id"] and not cancel.is_set():
                    return self.client("fish").speech(text,mood),"Fish fallback"
                raise
        def done(result):
            if token!=self.generation:return
            self.speaking=False
            if isinstance(result,Exception):self.set_status(str(result));return
            wav,label=result
            if not wav:self.set_status("Ready, Sir");return
            try:self.audio.play_wav(wav,float(self.store.settings["volume"]));self.set_status("Speaking · "+label)
            except RuntimeError as exc:self.set_status(str(exc))
        self.work(generate,done)

    @Slot()
    def testVoice(self):
        self.stop();self.speak("Hello, Sir. I’m Lisa. Ready when you are.","smile",self.generation)
    @Slot()
    def stop(self):
        self.generation+=1;self.cancel_event.set();self.cancel_event=threading.Event();demo.cancel();self.audio.stop_playback()
        if self.audio.recording:self.audio.stop_recording()
        self._busy=False;self.speaking=False;self.set_status("Ready, Sir")
    @Slot()
    def mic(self):
        if self.audio.recording:
            wav=self.audio.stop_recording();self._busy=True;token=self.generation;self.set_status("Transcribing…")
            def done(result):
                if token!=self.generation:return
                self._busy=False
                if isinstance(result,Exception):self.set_status(str(result));return
                if result:self.send(result)
                else:self.set_status("No speech heard. Try again.")
            client=self.client(self.store.settings["stt_provider"]);self.work(lambda:client.transcribe(wav),done)
        else:
            if self._busy:return
            provider=self.store.settings["stt_provider"]
            if not self.keys.get(provider) or not self.keys[provider].get():
                self.set_status("Add your "+provider.title()+" transcription key in Settings before using Mic.");return
            self.stop()
            try:self.audio.start_recording();self.started_recording=time.monotonic();self.set_status("Listening · press Mic to send")
            except RuntimeError as exc:self.set_status(str(exc))
    def tick(self):
        if self.closed:return
        if self.audio.recording and time.monotonic()-self.started_recording>=30:self.mic()
        if self._status.startswith("Speaking") and not self.audio.playing:self.set_status("Ready, Sir")
        current=(self.audio.recording,self.speaking or self.audio.playing,round(self.audio.level,2))
        if current!=self._last_audio:self._last_audio=current;self.activityChanged.emit()
        interval=60 if current[0] or current[1] else 350
        if self.timer.interval()!=interval:self.timer.setInterval(interval)

    @Slot(str)
    def setMood(self,mood):
        if mood not in MOODS:return
        # Expression artworks are grouped into four matching wardrobes.
        if mood!="smile":self.outfit=OUTFITS[MOODS.index(mood)//9]
        self.mood=mood;self.refresh();clip=self.cache.get(self.outfit,mood)
        if clip:self.clipChanged.emit(QUrl.fromLocalFile(str(clip)).toString())
        else:self.clipChanged.emit("")
    @Slot(str)
    def setOutfit(self,outfit):
        if outfit not in OUTFITS:return
        self.outfit=outfit;self.mood="smile";self.store.settings.update(outfit=outfit,auto_outfit=False);self.store.save();self.refresh();self.clipChanged.emit("")
        if self.store.settings["sound_enabled"]:self.audio.chime()
    @Slot(float,int)
    def saveLayout(self,zoom,width):
        layout={"zoom":round(max(.65,min(1.8,zoom)),3),"chat_width":max(290,min(700,width))}
        if any(self.store.settings.get(k)!=v for k,v in layout.items()):self.store.settings.update(layout);self.store.save()
    @Slot()
    def settings(self):SettingsDialog(self).exec()
    @Slot()
    def createDesktopShortcut(self):
        try:
            from installation import create_desktop_shortcut
            path=create_desktop_shortcut();self.set_status("Desktop shortcut created")
            QMessageBox.information(None,"Lisa · Desktop shortcut","Lisa is ready on your desktop."+("\n\n"+str(path) if path else ""))
        except (RuntimeError,OSError,ValueError) as exc:
            self.set_status(str(exc));QMessageBox.warning(None,"Lisa · Desktop shortcut",str(exc))
    @Slot()
    def memory(self):
        dialog=QDialog();dialog.setWindowTitle("Lisa · Memory");dialog.resize(600,460);dialog.setStyleSheet(STYLE);layout=QVBoxLayout(dialog)
        layout.addWidget(QLabel("Save only what you want Lisa to remember."));notes=QListWidget();notes.addItems(self.store.memories);layout.addWidget(notes);entry=QLineEdit();entry.setPlaceholderText("For example: Sir prefers tea");layout.addWidget(entry)
        row=QHBoxLayout();save=QPushButton("Save note");remove=QPushButton("Delete selected");row.addWidget(save);row.addWidget(remove);layout.addLayout(row)
        def add():
            self.store.add_memory(entry.text());entry.clear();notes.clear();notes.addItems(self.store.memories)
        def delete():
            i=notes.currentRow()
            if i>=0:self.store.memories.pop(i);self.store.save();notes.takeItem(i)
        save.clicked.connect(add);remove.clicked.connect(delete);dialog.exec()
    @Slot()
    def clearChat(self):
        if QMessageBox.question(None,"Clear chat","Clear this conversation? Saved memories stay.") == QMessageBox.StandardButton.Yes:
            self.stop();self._messages=[];self.add_message("assistant","Fresh start, Sir. What’s on your mind?")
    @Slot()
    def studio(self):
        dialog=QDialog();dialog.setWindowTitle("Lisa · Motion Studio");dialog.resize(680,480);dialog.setStyleSheet(STYLE);layout=QVBoxLayout(dialog)
        intro=QLabel("Create a smooth 4-second 1080p action with Vidu, or import your own clip. Generated clips have a fixed dark background. Generation uses your account credits.");intro.setWordWrap(True);layout.addWidget(intro)
        outfit=QComboBox();outfit.addItems(OUTFITS);outfit.setCurrentText(self.outfit);layout.addWidget(outfit)
        mood=QComboBox();mood.addItems(MOODS);mood.setCurrentText(self.mood);layout.addWidget(mood)
        status=QLabel("Saved clips: "+str(len(self.cache.clips))+" · pending jobs: "+str(len(self.jobs)));status.setWordWrap(True);layout.addWidget(status)
        generate=QPushButton("Generate with Vidu");importer=QPushButton("Import MP4 / WebM");preview=QPushButton("Play selected action");layout.addWidget(generate);layout.addWidget(importer);layout.addWidget(preview)
        def submit():
            m=mood.currentText();o=outfit.currentText() if m=="smile" else OUTFITS[MOODS.index(m)//9]
            if not self.keys["vidu"].get():status.setText("Add your Vidu API key in Settings first.");return
            if QMessageBox.question(dialog,"Generate video","Generate one 4-second 1080p Vidu clip for "+o+" / "+m+"? This spends Vidu credits.",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
            image=resource("assets/poses/"+m+".webp") if m!="smile" else resource("assets/portraits/"+o+".webp")
            client=self.client("vidu");generate.setEnabled(False);status.setText("Submitting…")
            def done(result):
                generate.setEnabled(True)
                if isinstance(result,Exception):status.setText(str(result));return
                self.jobs.append({"id":result,"outfit":o,"mood":m,"created":time.time()});self.store.write("motion-jobs.json",self.jobs);status.setText("Job saved. It will download when ready; you can close this studio.");self.set_status("Vidu generation queued")
            self.work(lambda:client.submit(image,m),done)
        def imported():
            path,_=QFileDialog.getOpenFileName(dialog,"Import an action clip","","Video (*.mp4 *.webm)")
            if not path:return
            try:
                m=mood.currentText();o=outfit.currentText() if m=="smile" else OUTFITS[MOODS.index(m)//9]
                self.cache.import_clip(path,o,m);status.setText("Clip saved for "+o+" / "+m+". Use Play selected action.")
            except ValueError as exc:status.setText(str(exc))
        def play():self.outfit=outfit.currentText();self.setMood(mood.currentText())
        generate.clicked.connect(submit);importer.clicked.connect(imported);preview.clicked.connect(play);dialog.exec()
    def poll_job(self):
        if self.polling or not self.jobs or not self.keys["vidu"].get():return
        job=dict(self.jobs[0]);self.polling=True;client=self.client("vidu")
        def poll():
            result=client.result(job["id"])
            if result.get("state")=="success":
                creations=result.get("creations",[])
                url=next((c.get("url") for c in creations if isinstance(c,dict) and c.get("url")),"")
                if not url:raise ApiError("Vidu completed without a video URL.")
                self.cache.download(url,job["outfit"],job["mood"])
            return result.get("state","")
        def done(result):
            self.polling=False
            if isinstance(result,Exception):self.set_status(str(result));self.motion_timer.stop();return
            if result in ("success","failed"):
                self.jobs=[j for j in self.jobs if j["id"]!=job["id"]];self.store.write("motion-jobs.json",self.jobs);self.set_status("Motion clip ready" if result=="success" else "Vidu generation failed. Check your account.")
                if result=="success" and self.outfit==job["outfit"] and self.mood==job["mood"]:self.setMood(self.mood)
        self.work(poll,done)
    @Slot()
    def checkUpdate(self):
        if self._updating:return
        self._updating=True;self._update_progress=-1;self._update_state="checking";self._update_note="Checking for a new Lisa…";self.updateChanged.emit();self.set_status("Checking updates…")
        def finish(note,state="idle"):
            self._updating=False;self._update_note=note;self._update_state=state;self._update_progress=-1;self.updateChanged.emit();self.set_status(note)
        def checked(result):
            if isinstance(result,Exception):finish(str(result),"error");return
            if not result:finish("You have the latest Lisa · "+VERSION,"success");return
            if QMessageBox.question(None,"Lisa update",result["version"]+" is ready. Download, install and restart Lisa? Your settings and memories will stay.",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:finish("Update available · "+result["version"]);return
            self._update_state="downloading";self._update_note="Downloading "+result["version"]+"…";self.updateChanged.emit();self.set_status(self._update_note)
            def downloaded(path):
                if isinstance(path,Exception):finish(str(path),"error");return
                try:
                    updates.install_update(path,self.store.directory);self._update_state="installing";self._update_note="Installing and restarting Lisa…";self.updateChanged.emit();self.app.quit()
                except (RuntimeError,OSError,ValueError) as exc:finish(str(exc),"error")
            self.work(lambda:updates.download_release(result,self.store.directory/"updates",lambda received,total:self.downloadProgress.emit(received,total)),downloaded)
        def check():
            from installation import is_installed
            return updates.latest_release(self.store.settings["repository"],prefer_installer=is_installed())
        self.work(check,checked)
    @Slot(int,int)
    def on_update_progress(self,received,total):
        if not self._updating:return
        self._update_progress=min(1,received/total) if total else -1
        self._update_note=(f"Downloading Lisa · {received/1048576:.1f} / {total/1048576:.1f} MB" if total else f"Downloading Lisa · {received/1048576:.1f} MB")
        self.updateChanged.emit()
    @Slot()
    def dismissUpdate(self):
        if not self._updating:self._update_note="";self.updateChanged.emit()
    def recover_update_status(self):
        record=updates.read_update_status(self.store.directory)
        if record.get("state") not in ("error","success"):return
        self._update_state=record["state"];self._update_note=record.get("message","Lisa update finished.");self.updateChanged.emit();self.set_status(self._update_note)
        if self._update_state=="error":QMessageBox.warning(None,"Lisa · Update needs attention",self._update_note+"\n\nYou can retry Update or run the latest Lisa installer.")
        updates.pending_update_error(self.store.directory,clear=True)
    @Slot()
    def quit(self):self.app.quit()
    def close(self):
        if self.closed:return
        self.stop();self.closed=True;self.timer.stop();self.motion_timer.stop();self.audio.close();self.store.save()


def main():
    app=QApplication(sys.argv);app.setApplicationName("LISA");app.setOrganizationName("Kitty Corp");app.setWindowIcon(QIcon(str(resource("assets/lisa.ico"))))
    QQuickStyle.setStyle("Basic");backend=Backend(app);engine=QQmlApplicationEngine();engine.rootContext().setContextProperty("lisa",backend);engine.load(QUrl.fromLocalFile(str(resource("ui/Main.qml"))))
    if not engine.rootObjects():return 2
    backend.window=engine.rootObjects()[0];app.aboutToQuit.connect(backend.close)
    if "--self-test" in sys.argv:
        backend.window.showNormal();backend.window.resize(1280,800)
        def capture():
            backend.window.grabWindow().save(str(backend.store.directory/"ui-self-test.png"))
            backend.setMood("commanding");backend.setOutfit("night");backend.close()
            (backend.store.directory/"self-test.json").write_text(json.dumps({"version":VERSION,"qml_loaded":True,"poses":len(MOODS),"microphone_closed":backend.audio.input_stream is None,"output_closed":backend.audio.output_stream is None}))
            app.quit()
        QTimer.singleShot(1600,capture)
    elif backend.store.settings["fullscreen"]:backend.window.showFullScreen()
    else:backend.window.show()
    if "--self-test" not in sys.argv:QTimer.singleShot(700,backend.recover_update_status)
    return app.exec()
