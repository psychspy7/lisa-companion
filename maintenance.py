"""Maintenance-only launch. Companion, providers and audio are never imported."""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
import threading
from PySide6.QtCore import QObject, Property, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication, QMessageBox
from core import VERSION, data_directory, resource
import updates

REPOSITORY = "psychspy7/lisa-companion"

class MaintenanceBackend(QObject):
    changed = Signal()
    completed = Signal(object, object)
    downloadProgress = Signal(int, int)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.directory = data_directory()
        self.closed = False
        self._busy = False
        self._note = "Check here for the next release."
        self._progress = -1.0
        self.completed.connect(self.dispatch)
        self.downloadProgress.connect(self.on_progress)

    @Property(str, constant=True)
    def version(self): return VERSION
    @Property(str, constant=True)
    def logo(self): return QUrl.fromLocalFile(str(resource("assets/lisa-logo.jpg"))).toString()
    @Property(bool, notify=changed)
    def busy(self): return self._busy
    @Property(str, notify=changed)
    def note(self): return self._note
    @Property(float, notify=changed)
    def progress(self): return self._progress

    def work(self, fn, callback):
        def run():
            try: result = fn()
            except Exception as exc: result = exc
            if not self.closed: self.completed.emit(callback, result)
        threading.Thread(target=run, daemon=True).start()

    @Slot(object, object)
    def dispatch(self, callback, result):
        if not self.closed: callback(result)

    def finish(self, note):
        self._busy = False
        self._progress = -1.0
        self._note = note
        self.changed.emit()

    @Slot()
    def checkUpdate(self):
        if self._busy or self.closed: return
        self._busy = True
        self._note = "Checking for the next Lisa release…"
        self._progress = -1.0
        self.changed.emit()
        def checked(result):
            if isinstance(result, Exception): self.finish(str(result)); return
            if not result: self.finish("The next update isn’t available yet. Please check again later."); return
            answer = QMessageBox.question(None, "Lisa update", result["version"] + " is available. Download, install and restart Lisa?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes: self.finish("Update available · " + result["version"]); return
            self._note = "Downloading " + result["version"] + "…"
            self.changed.emit()
            def downloaded(path):
                if isinstance(path, Exception): self.finish(str(path)); return
                self._note = "Preparing the update…"
                self.changed.emit()
                def prepared(result):
                    if isinstance(result, Exception): self.finish(str(result)); return
                    self.closed = True
                    self.app.quit()
                self.work(lambda: updates.install_update(path, self.directory), prepared)
            self.work(lambda: updates.download_release(result, self.directory / "updates", lambda received, total: self.downloadProgress.emit(received, total)), downloaded)
        def check():
            from installation import is_installed
            return updates.latest_release(REPOSITORY, prefer_installer=is_installed())
        self.work(check, checked)

    @Slot(int, int)
    def on_progress(self, received, total):
        self._progress = min(1.0, received / total) if total else -1.0
        self._note = (f"Downloading · {received / 1048576:.1f} / {total / 1048576:.1f} MB" if total else f"Downloading · {received / 1048576:.1f} MB")
        self.changed.emit()

    @Slot()
    def quit(self):
        self.closed = True
        self.app.quit()

def acknowledge_update(backend):
    """Retain the existing updater's verified restart handshake."""
    ack = os.environ.pop("LISA_UPDATE_ACK", "")
    expected = os.environ.pop("LISA_UPDATE_VERSION", "")
    if not ack or expected != VERSION: return
    path = Path(ack).resolve()
    if path.parent == (backend.directory / "updates").resolve() and path.name.startswith("launched-"):
        from updater_worker import write_json
        path.parent.mkdir(parents=True, exist_ok=True)
        write_json(path, {"version": VERSION, "pid": os.getpid(), "qml_loaded": True})

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LISA")
    app.setOrganizationName("Kitty Corp")
    app.setWindowIcon(QIcon(str(resource("assets/lisa.ico"))))
    QQuickStyle.setStyle("Basic")
    backend = MaintenanceBackend(app)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("maintenance", backend)
    engine.load(QUrl.fromLocalFile(str(resource("ui/Main.qml"))))
    if not engine.rootObjects(): return 2
    window = engine.rootObjects()[0]
    if "--self-test" in sys.argv:
        window.showNormal()
        window.resize(1280, 800)
        def capture():
            window.grabWindow().save(str(backend.directory / "ui-self-test.png"))
            forbidden = [name for name in ("audio", "sounddevice", "providers", "desktop", "motion") if name in sys.modules]
            report = {"version": VERSION, "qml_loaded": True, "maintenance": True, "companion_modules_loaded": forbidden, "microphone_started": False, "updater_available": hasattr(backend, "checkUpdate")}
            (backend.directory / "self-test.json").write_text(json.dumps(report), encoding="utf-8")
            app.quit()
        QTimer.singleShot(1200, capture)
    else: window.showFullScreen()
    QTimer.singleShot(600, lambda: acknowledge_update(backend))
    result = app.exec()
    backend.closed = True
    from shiboken6 import delete
    delete(engine)
    return result
