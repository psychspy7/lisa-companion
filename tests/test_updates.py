"""Updater integrity, release routing and Windows handoff regression tests."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import updates

REPO = "psychspy7/lisa-companion"
BASE = "https://github.com/" + REPO + "/releases/download/v1.0.0/"

class Response(io.BytesIO):
    def __init__(self, data=b"", url="", size=0):
        super().__init__(data)
        self.url = url
        self.headers = {"Content-Length": str(size)} if size else {}
    def geturl(self):
        return self.url

class ReliableUpdates(unittest.TestCase):
    def info(self, installer=False, **extra):
        name = "LISA-Setup.exe" if installer else "LISA.exe"
        return dict(repository=REPO, exe=BASE+name, checksum=BASE+"SHA256SUMS.txt", asset_name=name, version="v1.0.0", **extra)

    def release(self):
        return {"tag_name":"v1.0.0", "assets":[{"name":name,"browser_download_url":BASE+name} for name in ("LISA.exe","LISA-Setup.exe","SHA256SUMS.txt")]}

    def test_public_redirect_checks_updates_when_api_is_rate_limited(self):
        rate = urllib.error.HTTPError("https://api.github.com",403,"rate limit",{},io.BytesIO())
        with patch("updates.VERSION","0.3.0"), patch("updates.installed_edition",return_value=False), patch("urllib.request.urlopen",side_effect=[rate,Response(url="https://github.com/"+REPO+"/releases/tag/v1.0.0")]):
            result = updates.latest_release(REPO)
        self.assertEqual(result["asset_name"],"LISA.exe")
        self.assertEqual(result["version"],"v1.0.0")
        self.assertEqual(result["checksum"],BASE+"SHA256SUMS.txt")

    def test_installed_and_portable_editions_choose_the_correct_release_asset(self):
        for installed,name in ((True,"LISA-Setup.exe"),(False,"LISA.exe")):
            with patch("updates.VERSION","0.3.0"), patch("updates.installed_edition",return_value=installed), patch("urllib.request.urlopen",return_value=Response(json.dumps(self.release()).encode())):
                self.assertEqual(updates.latest_release(REPO)["asset_name"],name)

    def test_download_reports_progress_and_records_verified_integrity(self):
        payload = b"fake-executable" * 200000
        checksum = hashlib.sha256(payload).hexdigest()+"  LISA.exe\n"
        progress=[]
        with tempfile.TemporaryDirectory() as folder, patch("urllib.request.urlopen",side_effect=[Response(checksum.encode()),Response(payload,size=len(payload))]):
            target = updates.download_release(self.info(size=len(payload)),Path(folder),lambda current,total:progress.append((current,total)))
            self.assertEqual(target.read_bytes(),payload)
            record=json.loads(target.with_suffix(".json").read_text())
            self.assertEqual(record["sha256"],hashlib.sha256(payload).hexdigest())
            self.assertEqual(record["size"],len(payload))
            self.assertFalse(target.with_suffix(".part").exists())
        self.assertEqual(progress[0],(0,len(payload)))
        self.assertEqual(progress[-1],(len(payload),len(payload)))
        self.assertGreater(len(progress),2)

    def test_truncated_and_corrupt_files_are_removed(self):
        for payload,size,expected in ((b"partial",99,"incomplete"),(b"bad",3,"checksum did not match")):
            checksum = "a"*64+"  LISA.exe\n"
            with tempfile.TemporaryDirectory() as folder, patch("urllib.request.urlopen",side_effect=[Response(checksum.encode()),Response(payload)]):
                with self.assertRaisesRegex(updates.UpdateError,expected):
                    updates.download_release(self.info(size=size),Path(folder))
                self.assertEqual(list(Path(folder).iterdir()),[])

    def test_wrong_repo_mixed_releases_and_ambiguous_checksums_are_rejected(self):
        info=self.info();info["exe"]=info["exe"].replace(REPO,"someone/else")
        with tempfile.TemporaryDirectory() as folder, patch("urllib.request.urlopen") as request:
            with self.assertRaisesRegex(updates.UpdateError,"not from"):
                updates.download_release(info,Path(folder))
            request.assert_not_called()
        info=self.info();info["checksum"]=info["checksum"].replace("v1.0.0","v9.0.0")
        with self.assertRaisesRegex(updates.UpdateError,"different releases"):
            updates._validate_urls(info,"LISA.exe")
        with self.assertRaisesRegex(updates.UpdateError,"valid SHA-256"):
            updates._expected_checksum((("a"*64+"  LISA.exe\n")*2).encode(),"LISA.exe")

    def test_installer_download_uses_its_own_hash_and_name(self):
        payload=b"fake-setup";checksum=("a"*64+"  LISA.exe\n"+hashlib.sha256(payload).hexdigest()+"  LISA-Setup.exe\n").encode()
        with tempfile.TemporaryDirectory() as folder,patch("urllib.request.urlopen",side_effect=[Response(checksum),Response(payload)]):
            target=updates.download_release(self.info(installer=True),Path(folder))
            self.assertEqual(target.name,"LISA-Setup-new.exe")
            self.assertEqual(json.loads(target.with_suffix(".json").read_text())["kind"],"installer")

    def test_retry_and_actionable_network_errors(self):
        timeout=urllib.error.URLError("network disconnected")
        with patch("urllib.request.urlopen",side_effect=[timeout,Response(b"ready")]) as request,patch("updates.time.sleep"):
            with updates._open("https://github.com") as result:self.assertEqual(result.read(),b"ready")
            self.assertEqual(request.call_count,2)
        with tempfile.TemporaryDirectory() as folder,patch("urllib.request.urlopen",side_effect=timeout),patch("updates.time.sleep"):
            with self.assertRaisesRegex(updates.UpdateError,"internet connection"):
                updates.download_release(self.info(),Path(folder))
            self.assertEqual(list(Path(folder).iterdir()),[])

    def test_install_rechecks_hash_before_launching_helper(self):
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder);(directory/"updates").mkdir();source=directory/"updates/LISA-new.exe";source.write_bytes(b"good")
            source.with_suffix(".json").write_text(json.dumps({"size":4,"sha256":hashlib.sha256(b"good").hexdigest(),"kind":"portable"}))
            source.write_bytes(b"evil")
            with patch("updates.sys.frozen",True,create=True),patch("updates.sys.executable",str(directory/"LISA.exe")),patch("updates.subprocess.Popen") as launch:
                with self.assertRaisesRegex(updates.UpdateError,"changed"):
                    updates.install_update(source,directory)
                launch.assert_not_called()

    def test_helper_waits_uses_atomic_replace_retries_and_rollback(self):
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder);(directory/"updates").mkdir();source=directory/"updates/LISA-new.exe";source.write_bytes(b"good")
            source.with_suffix(".json").write_text(json.dumps({"size":4,"sha256":hashlib.sha256(b"good").hexdigest(),"kind":"portable"}))
            with patch("updates.sys.frozen",True,create=True),patch("updates.sys.executable",str(directory/"LISA.exe")),patch("updates.subprocess.Popen") as launch:
                updates.install_update(source,directory)
            helper=(directory/"install-update.ps1").read_text(encoding="utf-8-sig")
            self.assertIn("Wait-Process",helper);self.assertIn("-Timeout 90",helper)
            self.assertIn("[IO.File]::Replace",helper);self.assertIn("-lt 60",helper)
            self.assertIn("update-result.json",helper);self.assertIn("$lisaReplaced",helper)
            self.assertIn("Hidden",launch.call_args.args[0])

    def test_failed_install_diagnostics_survive_restart_and_can_be_cleared(self):
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder);(directory/"update-result.json").write_text(json.dumps({"status":"failed","message":"Disk is full"}),encoding="utf-8-sig")
            self.assertEqual(updates.pending_update_error(directory),"Disk is full")
            self.assertEqual(updates.pending_update_error(directory,clear=True),"Disk is full")
            self.assertEqual(updates.pending_update_error(directory),"")
            (directory/"update-error.txt").write_text("Legacy install failed")
            self.assertEqual(updates.pending_update_error(directory),"Legacy install failed")

    @unittest.skipUnless(os.name == "nt", "Windows update helper")
    def test_actual_windows_helper_replaces_file_and_keeps_backup_without_module_hash_command(self):
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder);(directory/"updates").mkdir()
            target=directory/"LISA.exe";target.write_bytes(b"previous version")
            source=directory/"updates/LISA-new.exe";source.write_bytes(b"new verified version")
            source.with_suffix(".json").write_text(json.dumps({"size":source.stat().st_size,"sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"kind":"portable"}))
            with patch("updates.sys.frozen",True,create=True),patch("updates.sys.executable",str(target)),patch("updates.subprocess.Popen"):
                updates.install_update(source,directory)
            helper=directory/"install-update.ps1"
            script=helper.read_text(encoding="utf-8-sig")
            # The test driver is still running; there is no old app process to await.
            script=script.replace(f"Get-Process -Id {os.getpid()}","Get-Process -Id 2147483647")
            script=script.replace(f"Wait-Process -Id {os.getpid()}","Wait-Process -Id 2147483647")
            # These tiny fixtures are data, so intercept only the final application launch.
            helper.write_text("function Start-Process { }\n"+script,encoding="utf-8-sig")
            result=subprocess.run(["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-WindowStyle","Hidden","-File",str(helper)],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(result.returncode,0,result.stderr.decode(errors="replace"))
            self.assertEqual(updates.read_update_status(directory)["state"],"success")
            self.assertEqual(target.read_bytes(),b"new verified version")
            self.assertEqual(target.with_suffix(".exe.bak").read_bytes(),b"previous version")

if __name__ == "__main__":unittest.main()
