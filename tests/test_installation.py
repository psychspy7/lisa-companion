import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from installation import installed_root, is_installed


class InstallationTests(unittest.TestCase):
    def test_marker_only_selects_valid_installed_app(self):
        with tempfile.TemporaryDirectory() as tmp:
            executable = str(Path(tmp) / "LISA.exe")
            marker = Path(tmp) / "install-state.json"
            with patch("installation.sys.executable", executable), patch("installation.sys.frozen", True, create=True):
                self.assertFalse(is_installed())
                for value in ("not json", '{}', '{"application":"OTHER","format":1}', '{"application":"LISA","format":2}'):
                    marker.write_text(value, encoding="utf-8")
                    self.assertFalse(is_installed())
                marker.write_text(json.dumps({"application": "LISA", "format": 1, "version": "1.0.0"}), encoding="utf-8")
                self.assertEqual(installed_root(), Path(tmp).resolve())

    def test_source_run_is_not_an_installed_binary(self):
        with patch("installation.sys.frozen", False, create=True):
            self.assertFalse(is_installed())
