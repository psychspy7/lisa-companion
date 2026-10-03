"""Per-user Windows installation detection and Desktop shortcut creation."""
from __future__ import annotations
import base64
import json
from pathlib import Path
import subprocess
import sys


def installed_root():
    if not getattr(sys, "frozen", False):
        return None
    root = Path(sys.executable).resolve().parent
    try:
        state = json.loads((root / "install-state.json").read_text(encoding="utf-8-sig"))
        if isinstance(state, dict) and state.get("application") == "LISA" and state.get("format") == 1:
            return root
    except (OSError, ValueError):
        pass
    return None


def is_installed():
    return installed_root() is not None


def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def create_desktop_shortcut():
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        raise RuntimeError("Desktop shortcuts are available in the Windows app.")
    target = Path(sys.executable).resolve()
    # Windows' known folder respects a Desktop redirected to OneDrive or another drive.
    script = (
        "$ErrorActionPreference='Stop';"
        "[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);"
        "$lisaDesktop=[Environment]::GetFolderPath('Desktop');"
        "if(-not $lisaDesktop){throw 'Desktop folder was not found'};"
        "$lisaShell=New-Object -ComObject WScript.Shell;"
        "$lisaShortcutPath=[IO.Path]::Combine($lisaDesktop,'LISA.lnk');"
        "$lisaLink=$lisaShell.CreateShortcut($lisaShortcutPath);"
        "$lisaLink.TargetPath=" + ps_quote(target) + ";"
        "$lisaLink.WorkingDirectory=" + ps_quote(target.parent) + ";"
        "$lisaLink.IconLocation=" + ps_quote(str(target) + ",0") + ";"
        "$lisaLink.Description='Talk to Lisa';$lisaLink.Save();Write-Output $lisaShortcutPath"
    )
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-EncodedCommand", encoded],
            check=True, capture_output=True, timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        raise RuntimeError("The shortcut could not be created. Check that your Desktop folder is writable.") from None
    return Path(result.stdout.decode("utf-8-sig").strip())
