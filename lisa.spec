"""Reproducible Windows bundle with only the QML modules Lisa uses."""
from pathlib import Path
import os
from PyInstaller.utils.hooks import collect_all

sound_data,sound_bins,sound_imports=collect_all("sounddevice")
sound_data.append((os.environ.get('LISA_UPDATER_EXE','dist/LISA-Updater.exe'),'updater'))
a=Analysis(["app.py"],pathex=[],binaries=sound_bins,
    datas=[("assets/portraits/*.webp","assets/portraits"),("assets/poses/*.webp","assets/poses"),("assets/lisa.ico","assets"),("assets/lisa-logo.jpg","assets"),("ui","ui"),("licenses","licenses"),("THIRD_PARTY_NOTICES.md","."),("version.json",".")]+sound_data,
    hiddenimports=["PySide6.QtQuick","PySide6.QtQml","PySide6.QtMultimedia"]+sound_imports,
    hookspath=["build_hooks"],excludes=["tkinter"],noarchive=False)

# Qt on supported Windows uses Windows ICU's unversioned exports. A Conda/Poppler ICU
# discovered on a developer machine has incompatible versioned exports. Never ship it.
a.binaries=[entry for entry in a.binaries if not (
    "poppler" in entry[1].lower() and Path(entry[0]).name.lower().startswith(("icuuc","icuin","icudt")))]
assert not any("qt6webenginecore" in entry[0].lower() for entry in a.binaries)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name="LISA",debug=False,
    bootloader_ignore_signals=False,strip=False,upx=False,console=False,
    disable_windowed_traceback=False,icon=["assets/lisa.ico"])
