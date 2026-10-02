"""GitHub release updates with a checksum and a hidden Windows replacement helper."""
import hashlib
import json
from pathlib import Path
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from core import VERSION, parse_repo


def version_tuple(value):
    return tuple(int(x) for x in value.removeprefix("v").split("-", 1)[0].split("."))


def latest_release(repo):
    repo = parse_repo(repo)
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases/latest", headers={"Accept": "application/vnd.github+json", "User-Agent": "LISA-Companion"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            release = json.loads(response.read(2_000_000))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError("No public release is available yet. Your current test version is ready to use. Future releases will appear here.") from None
        raise RuntimeError("GitHub could not check updates. Please try again later.") from None
    if version_tuple(release["tag_name"]) <= version_tuple(VERSION):
        return None
    assets = {a["name"]: a for a in release.get("assets", [])}
    if "LISA.exe" not in assets or "SHA256SUMS.txt" not in assets:
        raise RuntimeError("This release is missing its executable or checksum.")
    return {"version": release["tag_name"], "notes": release.get("body", ""), "exe": assets["LISA.exe"]["browser_download_url"],
            "checksum": assets["SHA256SUMS.txt"]["browser_download_url"], "url": release["html_url"], "repository": repo}


def download_release(info, destination: Path):
    destination.mkdir(parents=True, exist_ok=True)
    for url in (info["exe"], info["checksum"]):
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "github.com" or not parsed.path.startswith("/" + info["repository"] + "/releases/download/"):
            raise RuntimeError("The update download URL is not from the selected repository.")
    with urllib.request.urlopen(info["checksum"], timeout=30) as response:
        lines = response.read(10000).decode().splitlines()
    expected = next((line.split()[0].lower() for line in lines if len(line.split()) == 2 and line.split()[1].lstrip("*") == "LISA.exe"), "")
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise RuntimeError("The update has no valid SHA-256 checksum.")
    target = destination / "LISA-new.exe"
    digest = hashlib.sha256()
    total = 0
    try:
        with urllib.request.urlopen(info["exe"], timeout=60) as response, target.open("wb") as writer:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                total += len(block)
                if total > 200_000_000:
                    raise RuntimeError("The update exceeded the size limit.")
                digest.update(block)
                writer.write(block)
        if digest.hexdigest() != expected:
            raise RuntimeError("The update checksum did not match. The download was discarded.")
        return target
    except Exception:
        target.unlink(missing_ok=True)
        raise


def install_update(download: Path, helper_directory: Path):
    if not getattr(sys, "frozen", False):
        raise RuntimeError("Automatic installation is available in the packaged Windows app.")
    target = Path(sys.executable).resolve()
    source = download.resolve()
    if target.suffix.lower() != ".exe" or source.parent != (helper_directory / "updates").resolve():
        raise RuntimeError("Invalid update installation location.")
    def quote(path):
        return "'" + str(path).replace("'", "''") + "'"
    helper = helper_directory / "install-update.ps1"
    helper.write_text(f"""$ErrorActionPreference = 'Stop'
Wait-Process -Id {os.getpid()} -ErrorAction SilentlyContinue
$lisaTarget = {quote(target)}
$lisaSource = {quote(source)}
$lisaBackup = $lisaTarget + '.bak'
Copy-Item -LiteralPath $lisaTarget -Destination $lisaBackup -Force
try {{
  Copy-Item -LiteralPath $lisaSource -Destination $lisaTarget -Force
  Start-Process -FilePath $lisaTarget
}} catch {{
  Copy-Item -LiteralPath $lisaBackup -Destination $lisaTarget -Force
  Start-Process -FilePath $lisaTarget
}}
""", encoding="utf-8-sig")
    subprocess.Popen(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", str(helper)],
                     creationflags=subprocess.CREATE_NO_WINDOW)
