import json,tempfile,unittest,os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from core import VERSION
from immersive_desktop import SceneBridge,SuiteWindow
class StartupGate(unittest.TestCase):
 def test_voice_and_chat_wait_for_explicit_entry(self):
  backend=Mock();bridge=SimpleNamespace(backend=backend,session_entered=False)
  SceneBridge.send(bridge,"hello");SceneBridge.toggleVoice(bridge)
  backend.send.assert_not_called();backend.toggleConversation.assert_not_called()
  bridge.session_entered=True
  SceneBridge.send(bridge,"hello");SceneBridge.toggleVoice(bridge)
  backend.send.assert_called_once_with("hello");backend.toggleConversation.assert_called_once()
 def test_repeated_entry_does_not_repeat_initialization(self):
  bridge=SimpleNamespace(session_entered=False,backend=SimpleNamespace(scene_enabled=False),window=Mock())
  SceneBridge.entered(bridge);SceneBridge.entered(bridge)
  self.assertTrue(bridge.backend.scene_enabled);bridge.window.session_started.assert_called_once()
 def test_updater_acknowledges_ready_title_without_human_entry(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'updates').mkdir();ack=root/'updates/launched-test.json'
   window=SimpleNamespace(guard=Mock(),acknowledged=False,test=False,backend=SimpleNamespace(store=SimpleNamespace(directory=root),recover_update_status=Mock()))
   with patch.dict(os.environ,{'LISA_UPDATE_ACK':str(ack),'LISA_UPDATE_VERSION':VERSION}),patch('immersive_desktop.QTimer.singleShot'):
    SuiteWindow.scene_loaded(window)
   result=json.loads(ack.read_text());self.assertEqual(result['version'],VERSION);self.assertTrue(result['title_ready']);self.assertTrue(result['scene_loaded'])
 def test_update_ack_never_writes_outside_private_updates_folder(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);ack=root/'unexpected.json'
   window=SimpleNamespace(guard=Mock(),acknowledged=False,test=False,backend=SimpleNamespace(store=SimpleNamespace(directory=root),recover_update_status=Mock()))
   with patch.dict(os.environ,{'LISA_UPDATE_ACK':str(ack),'LISA_UPDATE_VERSION':VERSION}),patch('immersive_desktop.QTimer.singleShot'):
    SuiteWindow.scene_loaded(window)
   self.assertFalse(ack.exists())
if __name__=="__main__":unittest.main()
