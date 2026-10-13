import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core import Store, DEFAULTS
from motion import MotionCache, ViduClient

class ImmersiveBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def backend(self,folder):
        from desktop import Backend
        with patch.dict(os.environ,LISA_DATA_DIR=folder):
            backend=Backend(self.app);backend.store.settings['sound_enabled']=False;return backend

    def test_first_immersive_upgrade_preserves_api_choices_custom_prompt_and_memory(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'settings.json').write_text(json.dumps({'ui_version':4,'fullscreen':False,'chat_provider':'gemini','personality_prompt':'My Lisa','vidu_model':'my-model','auto_outfit':False,'outfit':'evening'}))
            (root/'memories.json').write_text('["I like chai"]')
            (root/'vidu.key').write_bytes(b'fake-encrypted-key')
            store=Store(root)
            self.assertTrue(store.settings['fullscreen'])
            self.assertEqual((store.settings['chat_provider'],store.settings['personality_prompt'],store.settings['vidu_model']),('gemini','My Lisa','my-model'))
            self.assertEqual(store.memories,['I like chai'])
            self.assertEqual((root/'vidu.key').read_bytes(),b'fake-encrypted-key')
            store.settings['fullscreen']=False;store.save()
            self.assertFalse(Store(root).settings['fullscreen'])

    def test_chat_emotion_keeps_selected_outfit_and_rig_but_explicit_pose_changes_it(self):
        with tempfile.TemporaryDirectory() as folder:
            backend=self.backend(folder);backend.setOutfit('evening');portrait=backend.portrait
            backend.setEmotion('angry')
            self.assertEqual(backend.outfit,'evening');self.assertEqual(backend.portrait,portrait)
            self.assertTrue(backend.avatarRigActive)
            backend.setMood('angry')
            self.assertEqual(backend.outfit,'afternoon');self.assertFalse(backend.avatarRigActive)
            backend.liveCharacter();self.assertTrue(backend.avatarRigActive);backend.close()

    def test_old_dark_clips_are_not_keyed_and_new_role_options_survive_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);video=root/'example.mp4';video.write_bytes(b'fake-video')
            cache=MotionCache(root);cache.import_clip(video,'evening','smile')
            self.assertFalse(MotionCache(root).green_screen('evening','smile'))
            cache.import_clip(video,'evening','talking',True)
            restored=MotionCache(root)
            self.assertTrue(restored.green_screen('evening','talking'))
            self.assertIsNotNone(restored.get('evening','talking'))

    def test_archived_video_is_not_started_or_loaded_by_native_backend(self):
        with tempfile.TemporaryDirectory() as folder:
            backend=self.backend(folder)
            self.assertNotIn("vidu",backend.keys)
            self.assertFalse(hasattr(backend,"motion_timer"))
            self.assertFalse(hasattr(backend,"cache"))
            backend.select_motion();self.assertEqual(backend.motionClip,"")
            backend.speaking=True;self.assertFalse(backend.playingSpeech)
            backend.audio.playing=True;backend.conversation_phase="speaking"
            self.assertTrue(backend.playingSpeech)
            backend.close()

    def test_green_vidu_generation_remains_one_explicit_silent_job(self):
        with patch('motion.stage_image',return_value='data:image/png;base64,fake'),patch('motion.request',return_value=b'{"task_id":"task-123"}') as request:
            ViduClient('fake',DEFAULTS).submit(Path('fake.webp'),'talking',True)
            body=request.call_args.args[3]
            self.assertEqual((body['duration'],body['audio'],body['bgm']),(4,False,False))
            self.assertIn('pure green',body['prompt']);self.assertIn('speaks naturally',body['prompt'])

if __name__=='__main__':unittest.main()
