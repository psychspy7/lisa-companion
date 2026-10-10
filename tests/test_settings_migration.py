import json
from pathlib import Path
import tempfile
import unittest

from core import Store, VERSION
from persona import DEFAULT_PERSONALITY, LEGACY_PERSONALITY


class SettingsMigration(unittest.TestCase):
    def test_upgrade_preserves_personal_data_and_custom_style(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            settings = {"ui_version": 3, "fullscreen": False, "personality_prompt": "My own Lisa", "chat_provider": "gemini", "save_history": True}
            (folder / "settings.json").write_text(json.dumps(settings))
            (folder / "memories.json").write_text('["I prefer chai"]')
            (folder / "history.json").write_text('[{"role":"user","content":"Hello"}]')
            (folder / "groq.key").write_bytes(b"encrypted test bytes")
            store = Store(folder)
            self.assertTrue(store.settings["fullscreen"])
            self.assertEqual(store.settings["ui_version"], 4)
            self.assertEqual(store.settings["personality_prompt"], "My own Lisa")
            self.assertEqual(store.settings["chat_provider"], "gemini")
            self.assertEqual(store.memories, ["I prefer chai"])
            self.assertEqual(store.history[0]["content"], "Hello")
            self.assertEqual((folder / "groq.key").read_bytes(), b"encrypted test bytes")
            store.settings["fullscreen"] = False
            store.save()
            self.assertFalse(Store(folder).settings["fullscreen"])

    def test_upgrade_replaces_only_legacy_stock_personality(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "settings.json").write_text(json.dumps({"ui_version": 3, "personality_prompt": LEGACY_PERSONALITY}))
            self.assertEqual(Store(folder).settings["personality_prompt"], DEFAULT_PERSONALITY)
            self.assertLessEqual(len(DEFAULT_PERSONALITY), 8000)

    def test_invalid_settings_shape_recovers_to_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "settings.json").write_text('["broken settings"]')
            self.assertTrue(Store(folder).settings["fullscreen"])
        self.assertEqual(VERSION, "1.9.3")


if __name__ == "__main__":
    unittest.main()
