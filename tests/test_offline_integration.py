import os,tempfile,unittest
from unittest.mock import patch,MagicMock
from PySide6.QtWidgets import QApplication
from desktop import Backend
from core import ApiError
def run_work(fn,cb):
 try:value=fn()
 except Exception as exc:value=exc
 cb(value)
class OfflineIntegration(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
 def backend(self,folder):
  with patch.dict(os.environ,{'LISA_DATA_DIR':folder}):b=Backend(self.app)
  for key in b.keys.values():key.get=MagicMock(return_value='')
  b.store.settings['voice_enabled']=False;b.offline.model=b.offline.model.parent/'missing.gguf'
  return b
 def test_no_keys_uses_grounded_local_companion_once(self):
  with tempfile.TemporaryDirectory() as folder:
   b=self.backend(folder);b.store.memories=['Likes tea']
   with patch.object(b,'work',side_effect=run_work):
    b.send('What do you remember about me?')
   self.assertIn('Likes tea',b.lastReply);self.assertEqual(b.modeName,'Offline companion');self.assertFalse(b.busy);b.close()
 def test_cloud_errors_fall_back_and_never_duplicate_user_message(self):
  with tempfile.TemporaryDirectory() as folder:
   b=self.backend(folder);b.keys['groq'].get.return_value='fake';client=MagicMock();client.chat.side_effect=ApiError('Invalid key')
   with patch.object(b,'client',return_value=client),patch.object(b,'work',side_effect=run_work):
    b.send('How you doing')
   self.assertIn('peaceful',b.lastReply);self.assertEqual(b.modeName,'Offline companion')
   self.assertEqual(sum(m['content']=='How you doing' for m in b.messages),1);b.close()
 def test_interrupt_ignores_old_offline_callback(self):
  with tempfile.TemporaryDirectory() as folder:
   b=self.backend(folder);callbacks=[]
   with patch.object(b,'work',side_effect=lambda fn,cb:callbacks.append(cb)):
    b.send('Tell me a story');b.stop();callbacks[0]({'reply':'late result','mood':'smile'})
   self.assertNotIn('late result',[m['content'] for m in b.messages]);self.assertFalse(b.busy);b.close()
 def test_stop_teasing_is_conversation_not_room_stop(self):
  with tempfile.TemporaryDirectory() as folder:
   b=self.backend(folder);b.scene_enabled=True
   with patch.object(b,'work',side_effect=run_work):
    b.send('Stop teasing');b.send('How you doing')
   self.assertFalse(b.offline.teasing);self.assertNotIn('peaceful evening',b.lastReply);b.close()
