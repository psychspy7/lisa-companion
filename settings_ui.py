"""Private native configuration; secrets never enter QML or conversation history."""
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QTabWidget,QWidget,QFormLayout,QLineEdit,QComboBox,QCheckBox,QPushButton,QLabel,QTextEdit,QDialogButtonBox,QMessageBox,QScrollArea)
from core import DEFAULTS,VERSION

STYLE="""QWidget{background:#171823;color:#eeeaf8;font:14px 'Segoe UI';} QLineEdit,QTextEdit,QComboBox{background:#232435;border:1px solid #41415c;border-radius:9px;padding:9px;} QLineEdit:focus,QTextEdit:focus,QComboBox:focus{border:1px solid #b49ad4;} QPushButton{background:#353048;border:1px solid #53506b;border-radius:9px;padding:10px 16px;} QPushButton:hover{background:#4c4568;} QPushButton:disabled{color:#777182;background:#242430;} QTabBar::tab{padding:12px;background:#222331;} QTabBar::tab:selected{background:#49405f;} QLabel{background:transparent;} QScrollArea{border:0;} QCheckBox{spacing:9px;padding:4px;} QDialogButtonBox{padding-top:8px;}"""


class SettingsDialog(QDialog):
    def __init__(self,backend):
        super().__init__(); self.backend=backend;self.fields={};self.keys={}
        self.finished.connect(lambda result:backend.stop())
        self.setWindowTitle("Lisa · Settings");self.resize(770,750);self.setStyleSheet(STYLE)
        layout=QVBoxLayout(self);layout.setContentsMargins(22,20,22,20);layout.setSpacing(14)
        title=QLabel("Make Lisa yours");title.setStyleSheet("font-size:24px;font-weight:600;");layout.addWidget(title)
        subtitle=QLabel("Chat, voice and the little details that make this your space.");subtitle.setStyleSheet("color:#a79bb9;");layout.addWidget(subtitle)
        tabs=QTabWidget();layout.addWidget(tabs)
        def page(name):
            widget=QWidget();form=QFormLayout(widget);form.setSpacing(14);scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(widget);tabs.addTab(scroll,name);return form
        def field(form,key,title,choices=None):
            value=backend.store.settings.get(key,DEFAULTS.get(key,""))
            if choices:
                control=QComboBox();control.setEditable(True);control.addItems(choices);control.setCurrentText(str(value))
            else: control=QLineEdit(str(value))
            form.addRow(title,control);self.fields[key]=control;return control
        def check(form,key,title):
            control=QCheckBox(title);control.setChecked(bool(backend.store.settings.get(key)));form.addRow(control);self.fields[key]=control
        def key(form,provider,title):
            row=QWidget();box=QHBoxLayout(row);box.setContentsMargins(0,0,0,0)
            control=QLineEdit();control.setEchoMode(QLineEdit.EchoMode.Password)
            control.setPlaceholderText("Saved securely · enter to replace" if backend.keys[provider].get() else "Enter your API key")
            self.keys[provider]=control;box.addWidget(control)
            remove=QPushButton("Forget");remove.clicked.connect(lambda: self.forget(provider,control));box.addWidget(remove);form.addRow(title,row)
        chat=page("Chat")
        field(chat,"chat_provider","Preferred chat service",["groq","gemini","openrouter","meta"])
        check(chat,"chat_fallback","Automatically try configured backups: Groq → Gemini → OpenRouter → Meta")
        for provider,title,models in (
            ("groq","Groq",["openai/gpt-oss-120b","openai/gpt-oss-20b","qwen/qwen3.8-27b"]),
            ("gemini","Google AI Studio",["gemini-3.5-flash-lite","gemini-3.8-flash","gemini-2.5-flash-lite"]),
            ("openrouter","OpenRouter",["openrouter/free"]),
            ("meta","Meta Llama",[""])):
            key(chat,provider,title+" API key")
            model=field(chat,provider+"_model",title+" model",models)
            row=QWidget();box=QHBoxLayout(row);box.setContentsMargins(0,0,0,0)
            load=QPushButton("Load models");test=QPushButton("Test connection")
            load.setObjectName(provider+"LoadModels");test.setObjectName(provider+"TestConnection")
            box.addWidget(load);box.addWidget(test);chat.addRow(row)
            load.clicked.connect(lambda checked=False,p=provider,m=model,b=load:self.load_models(m,b,p))
            test.clicked.connect(lambda checked=False,p=provider,b=test:self.test_connection(p,b))
        field(chat,"language","Conversation language",["Auto","English","Hindi","Hinglish"])
        check(chat,"demo_enabled","Use clearly labelled offline preview when chat key is missing")
        label=QLabel("A key alone does not guarantee model access or quota. Test each service separately. OpenRouter defaults to its free router; paid models use your account credits. Meta requires a Llama developer key, not a Facebook/WhatsApp token. Backups receive the same chat context and saved notes.");label.setWordWrap(True);chat.addRow(label)
        voice=page("Voice")
        check(voice,"voice_enabled","Speak Lisa's replies")
        field(voice,"voice_provider","Primary voice",["elevenlabs","fish","windows"])
        check(voice,"voice_fallback","Try the other configured cloud voice if the primary fails")
        check(voice,"windows_voice_fallback","Use the free Windows voice when cloud voices fail or are not configured")
        key(voice,"elevenlabs","ElevenLabs API key")
        eleven=field(voice,"eleven_voice_id","ElevenLabs Voice ID")
        eleven_model=field(voice,"eleven_model","ElevenLabs model",["eleven_flash_v2_5","eleven_multilingual_v2","eleven_v3","eleven_v4_turbo"])
        models_e=QPushButton("Load ElevenLabs speech models");voice.addRow(models_e);models_e.clicked.connect(lambda:self.load_models(eleven_model,models_e,"elevenlabs"))
        field(voice,"eleven_stt_model","ElevenLabs transcription",["scribe_v2","scribe_v1"])
        load_e=QPushButton("Choose an ElevenLabs voice");voice.addRow(load_e);load_e.clicked.connect(lambda:self.load_voices("elevenlabs",eleven,load_e))
        key(voice,"fish","Fish Audio API key");fish=field(voice,"fish_voice_id","Fish voice model ID")
        field(voice,"fish_model","Fish TTS model",["s2.1-pro-free","s2.1-pro"])
        load_f=QPushButton("Choose a Fish voice");voice.addRow(load_f);load_f.clicked.connect(lambda:self.load_voices("fish",fish,load_f))
        field(voice,"stt_provider","Preferred transcription",["groq","gemini","elevenlabs","fish"])
        check(voice,"stt_fallback","Use configured transcription backups if the preferred service fails")
        field(voice,"groq_stt_model","Groq transcription",["whisper-large-v3-turbo","whisper-large-v3"])
        field(voice,"gemini_stt_model","Gemini audio model",["gemini-3.5-flash-lite","gemini-3.8-flash","gemini-2.5-flash-lite"])
        field(voice,"fish_stt_model","Fish transcription model",["transcribe-1-pro"])
        for provider in ("elevenlabs","fish"):
            test=QPushButton("Test "+provider+" voice · uses a short greeting")
            voice.addRow(test);test.clicked.connect(lambda checked=False,p=provider,b=test:self.test_connection(p,b,voice=True))
        field(voice,"speech_pause","Pause before auto-send (seconds)")
        field(voice,"speech_threshold","Mic sensitivity threshold (0.003–0.15)")
        label=QLabel("Start talk enables hands-free turns: speak, pause, hear Lisa, speak again. Mic pauses during her reply to avoid echo. Mic / Interrupt lets you cut her off; Stop ends the session. Increase the threshold for a noisy room, lower it for a quiet voice.");label.setWordWrap(True);voice.addRow(label)
        motion=page("Motion")
        key(motion,"vidu","Vidu API key")
        field(motion,"vidu_model","Vidu video model",["viduq3-pro-fast","viduq3-turbo","viduq3-pro"])
        check(motion,"motion","Gentle breathing and character sway")
        label=QLabel("Open Motion Studio to generate a 4-second 1080p action clip, or import an MP4/WebM. Clips stay on this PC. Each Generate click uses your Vidu credits; no videos are generated automatically.");label.setWordWrap(True);motion.addRow(label)
        person=page("Personality")
        editor=QTextEdit();editor.setPlainText(backend.store.settings["personality_prompt"]);editor.setMinimumHeight(250);self.fields["personality_prompt"]=editor;person.addRow(editor)
        label=QLabel("Lisa's creator line: I am made by Virat by the help of Kitty Corp organisation.\n\nStyle changes the conversation. It cannot add PC tools or bypass a provider's rules.");label.setWordWrap(True);person.addRow(label)
        check(person,"pc_actions","Allow reviewed PC actions")
        privacy=page("App & privacy")
        shortcut=QPushButton("Add Lisa shortcut to my desktop");privacy.addRow(shortcut);shortcut.clicked.connect(backend.createDesktopShortcut)
        version=QLabel("LISA "+VERSION+" · Kitty Corp");version.setStyleSheet("color:#bda4dc;");privacy.addRow(version)
        check(privacy,"fullscreen","Open fullscreen next time")
        check(privacy,"auto_outfit","Change outfit with the time of day")
        check(privacy,"save_history","Save chat history locally")
        check(privacy,"sound_enabled","Soft interface chime")
        field(privacy,"repository","Update repository")
        update=QPushButton("Check for an update");privacy.addRow(update);update.setEnabled(not backend.updateInProgress);update.clicked.connect(lambda:(self.reject(),backend.checkUpdate()))
        label=QLabel("Microphone opens only after Mic or Start talk. Continuous talk listens between replies until you press Stop or quit. Every launch starts with the mic off. No camera. Keys are encrypted by Windows for your account. Memory is saved only through Memory.");label.setWordWrap(True);privacy.addRow(label)
        self.status=QLabel("");self.status.setWordWrap(True);layout.addWidget(self.status)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.save);buttons.rejected.connect(self.reject);layout.addWidget(buttons)

    def save_keys(self):
        pending=[(p,c.text().strip()) for p,c in self.keys.items() if c.text().strip()]
        for p,value in pending:self.backend.keys[p].validate(value)
        for p,value in pending:
            self.backend.keys[p].save(value);self.keys[p].clear();self.keys[p].setPlaceholderText("Saved securely · enter to replace")
        if pending:self.backend.refresh()

    def forget(self,provider,control):
        self.backend.keys[provider].forget();self.backend.refresh();control.clear();control.setPlaceholderText("Enter your API key");self.status.setText("Forgot "+provider+" key.")

    def save(self):
        try:
            self.save_keys()
            values=self.values()
            for name,low,high in (("speech_pause",.45,2.5),("speech_threshold",.003,.15)):
                try:value=float(values[name])
                except ValueError:raise ValueError("Enter a number for "+name.replace("_"," ")+".")
                if not low<=value<=high:raise ValueError(name.replace("_"," ").title()+f" must be {low}–{high}.")
            self.backend.store.settings.update(values)
            self.backend.store.save();self.backend.refresh();self.accept()
        except (ValueError,RuntimeError) as exc:self.status.setText(str(exc))

    def values(self):
        return {key:control.isChecked() if isinstance(control,QCheckBox) else control.currentText().strip() if isinstance(control,QComboBox) else control.toPlainText()[:8000] if isinstance(control,QTextEdit) else control.text().strip() for key,control in self.fields.items()}

    def test_connection(self,provider,button,voice=False):
        try:
            self.save_keys();settings=dict(self.backend.store.settings,**self.values());client=self.backend.client(provider,settings)
        except (ValueError,RuntimeError) as exc:self.status.setText(str(exc));return
        button.setEnabled(False);self.status.setText("Testing "+provider+"…")
        if voice:self.backend.stop()
        token=self.backend.generation
        def done(result):
            button.setEnabled(True)
            if isinstance(result,Exception):self.status.setText(str(result));return
            self.status.setText(provider+" connected successfully"+(" · voice ready" if voice else " · "+settings[provider+"_model"]))
            if voice and token==self.backend.generation:
                try:self.backend.audio.play_wav(result,float(settings["volume"]))
                except RuntimeError as exc:self.status.setText(str(exc))
        self.backend.work(lambda:client.speech("Hello, Sir. I’m Lisa.","smile") if voice else client.chat("Say hello in one short sentence.",[],[]),done)

    def load_models(self,model,button,provider="groq"):
        try:self.save_keys()
        except (ValueError,RuntimeError) as exc:self.status.setText(str(exc));return
        button.setEnabled(False);self.status.setText("Checking "+provider+"…")
        def done(result):
            button.setEnabled(True)
            if isinstance(result,Exception):self.status.setText(str(result));return
            if not result:self.status.setText("No models returned for this account.");return
            current=model.currentText();model.clear();model.addItems(result);model.setCurrentText(current if current in result else result[0]);self.status.setText("Loaded models. Select one, then Test connection to check access and quota.")
        self.backend.work(lambda:self.backend.client(provider).models(),done)

    def load_voices(self,provider,control,button):
        try:self.save_keys()
        except (ValueError,RuntimeError) as exc:self.status.setText(str(exc));return
        button.setEnabled(False);self.status.setText("Loading voices…")
        def done(result):
            button.setEnabled(True)
            if isinstance(result,Exception):self.status.setText(str(result));return
            from PySide6.QtWidgets import QInputDialog
            names=[v["name"]+" · "+v["voice_id"] for v in result]
            if not names:self.status.setText("No voices returned. Paste a Voice ID from your provider.");return
            selected,ok=QInputDialog.getItem(self,"Choose Lisa's voice","Voice",names,0,False)
            if ok:control.setText(result[names.index(selected)]["voice_id"])
            self.status.setText("Voice selected. Save, then use Test voice in the main window.")
        self.backend.work(lambda:self.backend.client(provider).voices(),done)
