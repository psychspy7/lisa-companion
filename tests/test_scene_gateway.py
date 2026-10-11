import json,tempfile,unittest,urllib.request,urllib.error
from pathlib import Path
from unittest.mock import patch
from scene_actions import scene_intent,validate_scene_action
from scene_server import SceneServer
from gateway import Gateway,StrictRedirect
from core import ApiError
class SceneAndGateway(unittest.TestCase):
 def test_closed_actions_and_conditional_invitation(self):
  self.assertEqual(scene_intent("Lisa go to the balcony"),"balcony")
  self.assertEqual(scene_intent("Put the whip back"),"put_whip_back")
  self.assertIsNone(scene_intent("Go to bed if you want"))
  self.assertIsNone(scene_intent("I like banana bread"))
  self.assertIsNone(scene_intent("I had tea earlier"))
  self.assertIsNone(scene_intent("What is your favourite tea?"))
  self.assertIsNone(scene_intent("I went to the balcony yesterday"))
  with self.assertRaises(ValueError):validate_scene_action("execute_shell")
 def test_asset_server_rejects_traversal_and_private_key_files(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);assets=root/'assets';assets.mkdir();(assets/'okay.js').write_text("test");(assets/'groq.key').write_text("private-test");(root/'outside.js').write_text("private")
   server=SceneServer(assets)
   try:
    url=server.url.split('/runtime')[0]
    with urllib.request.urlopen(url+'/okay.js') as r:self.assertIn("javascript",r.headers['Content-Type'])
    for path in ['/groq.key','/%2e%2e/outside.js']:
     with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(url+path)
   finally:server.close()
 def test_refresh_credential_is_protected_and_logout_removes_only_session(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'groq.key').write_bytes(b"existing")
   with patch('gateway.dpapi',side_effect=lambda data,decrypt=False:data[::-1]):
    gateway=Gateway(root);gateway.save({"id_token":"test-id-token","refresh_token":"private-refresh-token","expires_in":3600})
    self.assertNotIn(b"private-refresh-token",gateway.path.read_bytes())
    self.assertEqual(Gateway(root).token(),"test-id-token")
    gateway.logout();self.assertFalse(gateway.connected);self.assertFalse(gateway.path.exists());self.assertEqual((root/'groq.key').read_bytes(),b"existing")
 def test_redirect_does_not_forward_google_session_to_a_different_host(self):
  request=urllib.request.Request("https://lisa-control-center.kitty-ai.workers.dev/api/config",headers={"Authorization":"Bearer private-test"})
  with self.assertRaises(ApiError):StrictRedirect().redirect_request(request,None,302,"",{},"https://other.test/")
if __name__=="__main__":unittest.main()
