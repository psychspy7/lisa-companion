"""Maintenance cannot start companion services; update recovery remains available."""
import ast
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from unittest.mock import Mock
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
import maintenance

class MaintenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])

    def test_launch_has_no_companion_imports(self):
        tree = ast.parse(Path("app.py").read_text())
        self.assertEqual([n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)], ["maintenance"])
        tree = ast.parse(Path("maintenance.py").read_text())
        modules = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        modules += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        self.assertFalse(set(modules) & {"audio", "sounddevice", "desktop", "providers", "motion"})

    def test_constructor_preserves_personal_data(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, LISA_DATA_DIR=tmp):
            p = Path(tmp) / "settings.json"
            p.write_text('{"personal_setting":"keep"}')
            before = p.read_bytes()
            backend = maintenance.MaintenanceBackend(self.app)
            self.assertEqual(p.read_bytes(), before)
            self.assertFalse(hasattr(backend, "send"))
            self.assertTrue(callable(backend.checkUpdate))

    def test_latest_release_keeps_update_button_usable(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, LISA_DATA_DIR=tmp):
            backend = maintenance.MaintenanceBackend(self.app)
            def execute(fn, callback): callback(fn())
            with patch.object(backend, "work", side_effect=execute), patch("installation.is_installed", return_value=True), patch("updates.latest_release", return_value=None) as latest:
                backend.checkUpdate()
            latest.assert_called_once_with(maintenance.REPOSITORY, prefer_installer=True)
            self.assertFalse(backend.busy)
            self.assertIn("isn’t available", backend.note)

    def test_restart_ack_only_accepts_owned_update_path(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, LISA_DATA_DIR=tmp):
            backend = maintenance.MaintenanceBackend(self.app)
            target = Path(tmp) / "updates" / "launched-test.json"
            with patch.dict(os.environ, LISA_UPDATE_ACK=str(target), LISA_UPDATE_VERSION=maintenance.VERSION):
                maintenance.acknowledge_update(backend)
            self.assertEqual(json.loads(target.read_text())["version"], maintenance.VERSION)
            other = Path(tmp) / "unrelated.json"
            with patch.dict(os.environ, LISA_UPDATE_ACK=str(other), LISA_UPDATE_VERSION=maintenance.VERSION):
                maintenance.acknowledge_update(backend)
            self.assertFalse(other.exists())

    def test_future_release_installs_and_quits_maintenance(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, LISA_DATA_DIR=tmp):
            app = Mock()
            backend = maintenance.MaintenanceBackend(app)
            info = {"version": "v2.0.0"}
            download = Path(tmp) / "updates" / "LISA-Setup-new.exe"
            def execute(fn, callback): callback(fn())
            with patch.object(backend, "work", side_effect=execute), patch("installation.is_installed", return_value=True), patch("updates.latest_release", return_value=info), patch.object(maintenance.QMessageBox, "question", return_value=maintenance.QMessageBox.StandardButton.Yes), patch("updates.download_release", return_value=download) as fetch, patch("updates.install_update", return_value=None) as install:
                backend.checkUpdate()
            fetch.assert_called_once()
            install.assert_called_once_with(download, Path(tmp))
            app.quit.assert_called_once()
            self.assertTrue(backend.closed)
