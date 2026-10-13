import json,tempfile,unittest,urllib.request,urllib.error,os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from PySide6.QtCore import QObject,Signal
from PySide6.QtWidgets import QApplication
from godot_desktop import EngineBridge,EngineServer
from core import VERSION

class Dummy(QObject):
    sceneAction=Signal(str)
    def __init__(self,folder):
        super().__init__();self.lastReply="Hello";self.status="Ready";self.busy=False;self.recording=False;self.talking=False;self.conversation=False;self.audioLevel=0.;self.moodId="smile";self.updateProgress=-1;self.updateNote="";self.updateState="idle"
        self.store=SimpleNamespace(directory=Path(folder),settings={"camera_follow":True,"motion":True},save=Mock())
        for name in ("send","toggleConversation","recover_update_status","refresh","stop"):setattr(self,name,Mock())
        self.scene_enabled=False
class GodotBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def test_entry_is_required_before_chat_or_microphone(self):
        with tempfile.TemporaryDirectory() as folder:
            b=Dummy(folder);bridge=EngineBridge(b)
            bridge.dispatch("send","hello");bridge.dispatch("voice",None)
            b.send.assert_not_called();b.toggleConversation.assert_not_called()
            bridge.dispatch("enter",None);bridge.dispatch("send","hello");bridge.dispatch("voice",None)
            b.send.assert_called_once_with("hello");b.toggleConversation.assert_called_once()
            bridge.timer.stop()
    def test_follow_selection_persists_and_scene_events_are_ordered(self):
        with tempfile.TemporaryDirectory() as folder:
            b=Dummy(folder);bridge=EngineBridge(b)
            bridge.dispatch("follow",False);self.assertFalse(b.store.settings["camera_follow"]);b.store.save.assert_called_once()
            bridge.scene_action("balcony");bridge.scene_action("tea")
            self.assertEqual([v["action"] for v in bridge.snapshot(1)["events"]],["tea"])
            self.assertNotIn("key",json.dumps(bridge.snapshot()));bridge.timer.stop()
    def test_loopback_requires_nonce_and_rejects_web_origins_and_arbitrary_tools(self):
        with tempfile.TemporaryDirectory() as folder:
            bridge=EngineBridge(Dummy(folder));server=EngineServer(bridge)
            try:
                def request(path="/state",headers=None,data=None):
                    return urllib.request.urlopen(urllib.request.Request(server.url+path,headers=headers or {},data=data),timeout=3)
                with self.assertRaises(urllib.error.HTTPError) as e:request()
                self.assertEqual(e.exception.code,403)
                auth={"Authorization":"Bearer "+server.token}
                self.assertEqual(json.load(request(headers=auth))["version"],VERSION)
                with self.assertRaises(urllib.error.HTTPError) as e:request(headers={**auth,"Origin":"https://example.com"})
                self.assertEqual(e.exception.code,403)
                for value in ({"name":"shell","value":"anything"},{"name":"send","value":"x"*4001},{"name":"follow","value":"false"}):
                    with self.assertRaises(urllib.error.HTTPError) as e:request("/command",auth,json.dumps(value).encode())
                    self.assertEqual(e.exception.code,400)
            finally:server.close();bridge.timer.stop()
    def test_ready_acknowledges_the_engine_without_starting_microphone(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/"updates").mkdir();ack=root/"updates/launched-godot.json"
            b=Dummy(folder);bridge=EngineBridge(b)
            with patch.dict(os.environ,{"LISA_UPDATE_ACK":str(ack),"LISA_UPDATE_VERSION":VERSION}):
                bridge.dispatch("ready",None)
            record=json.loads(ack.read_text())
            self.assertTrue(record["scene_loaded"]);self.assertEqual(record["engine"],"Godot Standard");self.assertFalse(bridge.entered)
            b.toggleConversation.assert_not_called();bridge.timer.stop()
if __name__=="__main__":unittest.main()
