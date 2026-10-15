import os,tempfile,unittest,json,sys
from pathlib import Path
from unittest.mock import patch,Mock
from types import SimpleNamespace
from PySide6.QtWidgets import QApplication
from activation_ui import ActivationDialog
from godot_desktop import EngineBridge
from tests.test_godot_bridge import Dummy
class ActivationStartup(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
 def test_legacy_flag_cannot_select_ungated_ui(self):
  import desktop
  with patch.object(sys,'argv',['LISA.exe','--legacy-ui']),patch('godot_desktop.main',return_value=7) as native,patch.object(desktop,'qml_main') as legacy:
   self.assertEqual(desktop.main(),7);native.assert_called_once_with(desktop.Backend);legacy.assert_not_called()
 def test_visible_activation_screen_ack_does_not_claim_engine_or_unlock_chat(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'updates').mkdir();ack=root/'updates/launched-gate.json'
   b=Dummy(folder);bridge=EngineBridge(b)
   license=SimpleNamespace(purchase_url='https://kittycorp.vercel.app/')
   dialog=ActivationDialog(b,license,lambda:bridge.acknowledge(True))
   with patch.dict(os.environ,{'LISA_UPDATE_ACK':str(ack),'LISA_UPDATE_VERSION':bridge.snapshot()['version']}):
    dialog.show()
    for _ in range(4):self.app.processEvents()
   self.assertTrue(ack.exists());record=json.loads(ack.read_text())
   self.assertTrue(record['activation_required']);self.assertFalse(record['scene_loaded']);self.assertFalse(bridge.entered)
   b.send.assert_not_called();b.toggleConversation.assert_not_called();dialog.reject();bridge.timer.stop()
