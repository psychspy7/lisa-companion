"""Verified GitHub updates for portable and installed Lisa editions."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from core import ApiError, VERSION, parse_repo

MAX_DOWNLOAD = 1_500_000_000
INSTALL_MARKER = "install-state.json"

class UpdateError(ApiError, RuntimeError):
    """An actionable message preserved by the desktop worker."""


def version_tuple(value):
    match = re.fullmatch(r"v?(\d+)\.(\d+)(?:\.(\d+))?", str(value))
    if not match:
        raise UpdateError("The release has an invalid version. Open the release page to check it.")
    return tuple(int(part or 0) for part in match.groups())


def installed_edition(executable=None):
    target = Path(executable or sys.executable).resolve()
    try:
        marker = json.loads((target.parent / INSTALL_MARKER).read_text(encoding="utf-8-sig"))
        return marker.get("application") == "LISA" and marker.get("format") == 1
    except (OSError, ValueError, AttributeError):
        return False


def _open(url, timeout=30):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "LISA-Companion/" + VERSION})
    for attempt in range(3):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt == 2:
                raise
        time.sleep(.4 * (attempt + 1))


def _network_error(exc, operation):
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code == 404:
            return UpdateError("The update file is not available yet. Try again shortly, or open the release page.")
        if exc.code in (403, 429):
            return UpdateError("GitHub temporarily limited update requests. Please wait a few minutes and try again.")
        return UpdateError(f"GitHub could not {operation} (HTTP {exc.code}). Please try again.")
    return UpdateError(f"Lisa could not {operation}. Check your internet connection and try again.")


def _fallback_release(repo):
    # GitHub's public redirect works independently of the API's unauthenticated quota.
    with _open(f"https://github.com/{repo}/releases/latest", timeout=20) as response:
        final = urllib.parse.urlparse(response.geturl())
        prefix = f"/{repo}/releases/tag/"
        if final.scheme != "https" or final.hostname != "github.com" or not final.path.startswith(prefix):
            raise UpdateError("GitHub did not return a valid public Lisa release.")
        tag = urllib.parse.unquote(final.path[len(prefix):])
        version_tuple(tag)
        base = f"https://github.com/{repo}/releases/download/{urllib.parse.quote(tag, safe='')}"
        return {"tag_name": tag, "body": "", "html_url": f"https://github.com/{repo}/releases/tag/{urllib.parse.quote(tag, safe='')}",
                "assets": [{"name": name, "browser_download_url": base + "/" + name}
                           for name in ("LISA.exe", "LISA-Setup.exe", "SHA256SUMS.txt")]}


def latest_release(repo, prefer_installer=None):
    repo = parse_repo(repo)
    try:
        with _open(f"https://api.github.com/repos/{repo}/releases/latest", timeout=20) as response:
            release = json.loads(response.read(2_000_001))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        if isinstance(exc, urllib.error.HTTPError) and exc.code == 404:
            raise UpdateError("No public release is available yet. Your current Lisa is ready to use.") from None
        try:
            release = _fallback_release(repo)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as fallback:
            raise _network_error(fallback, "check updates") from None
    except (ValueError, UnicodeError):
        raise UpdateError("GitHub returned an unreadable release. Please try again.") from None
    if not isinstance(release, dict) or not release.get("tag_name"):
        raise UpdateError("GitHub returned an incomplete release. Please try again.")
    if version_tuple(release["tag_name"]) <= version_tuple(VERSION):
        return None
    assets = {a.get("name"): a for a in release.get("assets", []) if isinstance(a, dict)}
    installed = installed_edition() if prefer_installer is None else bool(prefer_installer)
    name = "LISA-Setup.exe" if installed else "LISA.exe"
    if name not in assets or "SHA256SUMS.txt" not in assets:
        raise UpdateError("This release is missing its " + name + " or checksum. Please open the release page.")
    try:
        return {"version": release["tag_name"], "notes": str(release.get("body") or "")[:8000],
                "exe": assets[name]["browser_download_url"], "checksum": assets["SHA256SUMS.txt"]["browser_download_url"],
                "url": release.get("html_url", f"https://github.com/{repo}/releases/latest"), "repository": repo,
                "asset_name": name, "kind": "installer" if name == "LISA-Setup.exe" else "portable",
                "installer": installed,
                "size": int(assets[name].get("size") or 0)}
    except (KeyError, ValueError, TypeError):
        raise UpdateError("GitHub returned incomplete update files. Please try again.") from None


def _validate_urls(info, name):
    repo = parse_repo(info["repository"])
    parents = []
    for key, filename in (("exe", name), ("checksum", "SHA256SUMS.txt")):
        parsed = urllib.parse.urlparse(info[key])
        prefix = "/" + repo + "/releases/download/"
        if (parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.query or parsed.fragment
                or not parsed.path.startswith(prefix) or parsed.path.rsplit("/", 1)[-1] != filename
                or "/../" in parsed.path or "/./" in parsed.path):
            raise UpdateError("The update download URL is not from the selected repository.")
        parents.append(parsed.path.rsplit("/", 1)[0])
    if parents[0] != parents[1]:
        raise UpdateError("The update executable and checksum belong to different releases.")


def _expected_checksum(raw, name):
    try:
        lines = raw.decode("utf-8-sig").splitlines()
    except UnicodeError:
        raise UpdateError("The update has no valid SHA-256 checksum.") from None
    hashes = [fields[0].lower() for line in lines if len(fields := line.split()) == 2 and fields[1].lstrip("*") == name]
    if len(hashes) != 1 or not re.fullmatch(r"[0-9a-f]{64}", hashes[0]):
        raise UpdateError("The update has no valid SHA-256 checksum.")
    return hashes[0]


def _hash_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_release(info, destination: Path, progress=None):
    name = info.get("asset_name", "LISA.exe")
    if name not in ("LISA.exe", "LISA-Setup.exe"):
        raise UpdateError("This release uses an unsupported update file.")
    _validate_urls(info, name)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / ("LISA-Setup-new.exe" if name == "LISA-Setup.exe" else "LISA-new.exe")
    part = target.with_suffix(".part")
    metadata = target.with_suffix(".json")
    target.unlink(missing_ok=True)
    metadata.unlink(missing_ok=True)
    try:
        with _open(info["checksum"]) as response:
            raw = response.read(100_001)
        if len(raw) > 100_000:
            raise UpdateError("The release checksum file is too large.")
        expected = _expected_checksum(raw, name)
        digest = hashlib.sha256()
        total = 0
        with _open(info["exe"], timeout=60) as response, part.open("wb") as writer:
            announced = int(info.get("size") or 0)
            header_size = int(getattr(response, "headers", {}).get("Content-Length", "0") or 0)
            expected_size = announced or header_size
            if expected_size < 0 or expected_size > MAX_DOWNLOAD:
                raise UpdateError("The update exceeded the size limit.")
            if announced and header_size and announced != header_size:
                raise UpdateError("GitHub returned an unexpected update size. Please try again.")
            if progress:
                progress(0, expected_size)
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                total += len(block)
                if total > MAX_DOWNLOAD or (expected_size and total > expected_size):
                    raise UpdateError("The update exceeded the size limit.")
                digest.update(block)
                writer.write(block)
                if progress:
                    progress(total, expected_size)
            writer.flush()
            os.fsync(writer.fileno())
        if not total or (expected_size and total != expected_size):
            raise UpdateError("The update download was incomplete. Please try again.")
        if digest.hexdigest() != expected:
            raise UpdateError("The update checksum did not match. The download was discarded.")
        part.replace(target)
        record = {"sha256": expected, "size": total, "kind": "installer" if name == "LISA-Setup.exe" else "portable",
                  "version": info.get("version", ""), "asset_name": name}
        metadata.write_text(json.dumps(record), encoding="utf-8")
        return target
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise _network_error(exc, "download the update") from None
    except OSError:
        raise UpdateError("Lisa could not save the update. Check free disk space and folder permissions.") from None
    finally:
        part.unlink(missing_ok=True)
        if not metadata.exists():
            target.unlink(missing_ok=True)


def pending_update_error(helper_directory, clear=False):
    directory = Path(helper_directory)
    result, legacy = directory / "update-result.json", directory / "update-error.txt"
    message = ""
    try:
        record = json.loads(result.read_text(encoding="utf-8-sig"))
        if record.get("status") == "failed":
            message = str(record.get("message") or "Lisa could not install the update. Please run the latest Lisa Setup.")[:1200]
    except (OSError, ValueError, AttributeError):
        pass
    if not message:
        try:
            message = legacy.read_text(encoding="utf-8-sig")[:1200]
        except OSError:
            pass
    if clear:
        result.unlink(missing_ok=True)
        legacy.unlink(missing_ok=True)
    return message


def read_update_status(helper_directory):
    directory = Path(helper_directory)
    try:
        record = json.loads((directory / "update-result.json").read_text(encoding="utf-8-sig"))
        if isinstance(record, dict):
            return {"state": "error" if record.get("status") == "failed" else record.get("status", ""),
                    "message": str(record.get("message", ""))[:1200], "version": str(record.get("version", ""))}
    except (OSError, ValueError):
        pass
    message = pending_update_error(directory)
    return {"state": "error", "message": message} if message else {}


def _quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def install_update(download: Path, helper_directory: Path):
    if not getattr(sys, "frozen", False):
        raise UpdateError("Automatic installation is available in the packaged Windows app.")
    target, source, directory = Path(sys.executable).resolve(), Path(download).resolve(), Path(helper_directory).resolve()
    if target.suffix.lower() != ".exe" or source.parent != directory / "updates":
        raise UpdateError("Invalid update installation location.")
    try:
        record = json.loads(source.with_suffix(".json").read_text(encoding="utf-8"))
        if source.stat().st_size != record["size"] or _hash_file(source) != record["sha256"]:
            raise UpdateError("The downloaded update changed. Download it again before installing.")
        kind = record["kind"]
        if kind not in ("portable", "installer") or (kind == "installer") != installed_edition(target):
            raise UpdateError("This update does not match your Lisa edition. Please run the latest Lisa Setup.")
    except (OSError, ValueError, KeyError, TypeError):
        raise UpdateError("The verified update record is missing. Please download the update again.") from None
    directory.mkdir(parents=True, exist_ok=True)
    pending_update_error(directory, clear=True)
    helper = directory / "install-update.ps1"
    portable = """
    $lisaStage = $lisaTarget + '.new'
    for ($lisaAttempt = 0; $lisaAttempt -lt 60; $lisaAttempt++) {
      try {
        Copy-Item -LiteralPath $lisaSource -Destination $lisaStage -Force
        if ((Get-LisaHash $lisaStage) -ne $lisaExpected) { throw 'The staged update failed its checksum.' }
        [IO.File]::Replace($lisaStage, $lisaTarget, $lisaBackup, $true)
        $lisaReplaced = $true
        break
      } catch {
        if ($lisaAttempt -eq 59) { throw }
        Start-Sleep -Milliseconds 500
      }
    }
    if ((Get-LisaHash $lisaTarget) -ne $lisaExpected) { throw 'The installed update failed its checksum.' }
"""
    installer = """
    $lisaArguments = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /UPDATE /DIR="' + (Split-Path -Parent $lisaTarget) + '"'
    $lisaSetup = Start-Process -FilePath $lisaSource -ArgumentList $lisaArguments -WindowStyle Hidden -PassThru -Wait
    if ($lisaSetup.ExitCode -ne 0) { throw ('Lisa Setup could not finish (exit ' + $lisaSetup.ExitCode + '). Run the latest Lisa Setup manually.') }
    if (-not (Test-Path -LiteralPath $lisaTarget)) { throw 'Lisa Setup did not install the application. Run the latest Lisa Setup manually.' }
"""
    helper.write_text(f"""$ErrorActionPreference = 'Stop'
$lisaTarget = {_quote(target)}
$lisaSource = {_quote(source)}
$lisaExpected = {_quote(record['sha256'])}
$lisaBackup = $lisaTarget + '.bak'
$lisaResult = {_quote(directory / 'update-result.json')}
$lisaReplaced = $false
function Get-LisaHash($lisaFile) {{
  $lisaHasher = [Security.Cryptography.SHA256]::Create()
  $lisaStream = [IO.File]::OpenRead($lisaFile)
  try {{ return ([BitConverter]::ToString($lisaHasher.ComputeHash($lisaStream))).Replace('-', '').ToLowerInvariant() }}
  finally {{ $lisaStream.Dispose(); $lisaHasher.Dispose() }}
}}
function Write-LisaResult($status, $message) {{
  @{{status=$status; message=$message; version={_quote(record.get('version',''))}}} | ConvertTo-Json | Set-Content -LiteralPath $lisaResult -Encoding UTF8
}}
try {{
  $lisaParent = Get-Process -Id {os.getpid()} -ErrorAction SilentlyContinue
  if ($lisaParent) {{ Wait-Process -Id {os.getpid()} -Timeout 90 -ErrorAction SilentlyContinue }}
  if (Get-Process -Id {os.getpid()} -ErrorAction SilentlyContinue) {{ throw 'Lisa is still running. Close it before installing the update.' }}
  if ((Get-LisaHash $lisaSource) -ne $lisaExpected) {{ throw 'The update failed its checksum. Download it again.' }}
{installer if kind == 'installer' else portable}
  Write-LisaResult 'success' 'Lisa was updated successfully.'
  Start-Process -FilePath $lisaTarget -WorkingDirectory (Split-Path -Parent $lisaTarget) -WindowStyle Normal
}} catch {{
  $lisaFailure = $_.Exception.Message
  if ($lisaReplaced -and (Test-Path -LiteralPath $lisaBackup)) {{
    try {{ [IO.File]::Replace($lisaBackup, $lisaTarget, $null, $true) }} catch {{ $lisaFailure += ' Restore Lisa from the latest Setup if it will not open.' }}
  }}
  Write-LisaResult 'failed' ('Update failed: ' + $lisaFailure)
  if (Test-Path -LiteralPath $lisaTarget) {{ Start-Process -FilePath $lisaTarget -WorkingDirectory (Split-Path -Parent $lisaTarget) -WindowStyle Normal }}
}}
""", encoding="utf-8-sig")
    try:
        subprocess.Popen(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", str(helper)],
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except OSError:
        raise UpdateError("Windows could not start the update installer. Run the latest Lisa Setup manually.") from None
