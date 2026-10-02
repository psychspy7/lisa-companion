import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch,MagicMock
from core import DEFAULTS,Credentials,ApiError,wav_from_pcm,SYSTEM_PROMPT
from providers import GroqClient,FishClient,request,validate_reply,character_instructions
from actions import validate_action,explicit_local_action,open_target
from motion import ViduClient,MotionCache


class UpgradeContracts(unittest.TestCase):
    def test_groq_structured_chat_preserves_custom_style_creator_and_notes(self):
        result={"choices":[{"finish_reason":"stop","message":{"content":json.dumps({"reply":"On it, Sir.","mood":"listening","action":{"type":"open_app","value":"calculator"}})}}]}
        settings=dict(DEFAULTS,personality_prompt="Use warm Hinglish banter.")
        with patch("urllib.request.urlopen",return_value=io.BytesIO(json.dumps(result).encode())) as send:
            answer=GroqClient("private-test-key",settings).chat("Open calculator",[],["Sir prefers tea"])
            req=send.call_args.args[0];body=json.loads(req.data)
            self.assertEqual(req.get_header("Authorization"),"Bearer private-test-key")
            self.assertNotIn("private-test",req.full_url)
            self.assertEqual(body["response_format"],{"type":"json_object"})
            self.assertIn("Use warm Hinglish banter",body["messages"][0]["content"])
            self.assertIn("I am made by Virat by the help of Kitty Corp organisation.",body["messages"][0]["content"])
            self.assertIn("Sir prefers tea",body["messages"][0]["content"])
            self.assertEqual(answer["action"]["value"],"calculator")

    def test_groq_incomplete_response_is_not_spoken(self):
        for finish,content in (("length",'{"reply":"Hi","mood":"smile"}'),("stop","not JSON"),("stop",'{"reply":"Hi","mood":"unknown"}')):
            result={"choices":[{"finish_reason":finish,"message":{"content":content}}]}
            with patch("providers.request",return_value=json.dumps(result).encode()):
                with self.assertRaises(ApiError):GroqClient("fake",DEFAULTS).chat("Hi",[],[])

    def test_models_are_loaded_from_groq_and_nonchat_models_are_excluded(self):
        with patch("providers.request",return_value=b'{"data":[{"id":"llama-3.3-70b-versatile"},{"id":"whisper-large-v3-turbo"},{"id":"openai/gpt-oss-20b"}]}'):
            self.assertEqual(GroqClient("fake",DEFAULTS).models(),["llama-3.3-70b-versatile","openai/gpt-oss-20b"])

    def test_fish_s2_voice_uses_bracket_emotion_and_separate_auth(self):
        client=FishClient("fish-private",dict(DEFAULTS,fish_voice_id="example-voice"))
        with patch("providers.request",return_value=wav_from_pcm(b"\x00\x00"*500)) as send:
            audio=client.speech("Sir, take your time.","caring")
            self.assertTrue(audio.startswith(b"RIFF"));body=send.call_args.args[3]
            self.assertTrue(body["text"].startswith("[empathetic]"))
            self.assertEqual(body["reference_id"],"example-voice")
            self.assertEqual(send.call_args.kwargs["extra_headers"],{"model":"s2.1-pro-free"})

    def test_transcription_multipart_matches_each_provider_contract(self):
        wav=wav_from_pcm(b"\x00\x00"*500)
        for cls,field in ((GroqClient,b'name="file"'),(FishClient,b'name="audio"')):
            with patch("providers.request",return_value=b'{"text":"Namaste Sir"}') as send:
                self.assertEqual(cls("fake",DEFAULTS).transcribe(wav),"Namaste Sir")
                self.assertIn(field,send.call_args.args[3]);self.assertIn(wav,send.call_args.args[3])

    def test_every_new_key_is_encrypted_separately(self):
        with tempfile.TemporaryDirectory() as folder:
            for provider in ("groq","fish","vidu"):
                key="fake-not-real-"+provider+"-123456789"
                c=Credentials(Path(folder),provider);c.save(key)
                self.assertNotIn(key.encode(),c.path.read_bytes());self.assertEqual(Credentials(Path(folder),provider).get(),key)

    def test_pc_actions_reject_arbitrary_commands_and_private_urls(self):
        for action in ({"type":"shell","value":"echo hello"},{"type":"open_app","value":"powershell"},{"type":"open_url","value":"file:///C:/Windows"},{"type":"open_url","value":"https://127.0.0.1/a"},{"type":"open_url","value":"https://example.com:8080"},{"type":"open_url","value":"https://key@example.com"}):
            with self.subTest(action=action),self.assertRaises(ValueError):validate_action(action)
        self.assertEqual(validate_action({"type":"open_url","value":"https://example.com/path"}),("open_url","https://example.com/path"))
        self.assertIsNone(explicit_local_action("Do you like calculator apps?"))
        self.assertEqual(explicit_local_action("Please open calculator.")["value"],"calculator")
        with patch("actions.subprocess.Popen") as launch:
            open_target("open_app","calculator");self.assertEqual(launch.call_args.args[0],["calc.exe"]);self.assertFalse(launch.call_args.kwargs["shell"])

    def test_vidu_payload_is_one_explicit_silent_short_video(self):
        with patch("motion.stage_image",return_value="data:image/png;base64,fake"),patch("motion.request",return_value=b'{"task_id":"task-123","state":"created"}') as send:
            self.assertEqual(ViduClient("fake",DEFAULTS).submit(Path("fake.png"),"kiss"),"task-123")
            body=send.call_args.args[3]
            self.assertEqual((body["duration"],body["resolution"],body["audio"],body["is_rec"]),(4,"1080p",False,False))
            self.assertIn("flying kiss",body["prompt"])
        with patch("urllib.request.urlopen",return_value=io.BytesIO(b'{"state":"processing"}')) as send:
            ViduClient("private-vidu",DEFAULTS).result("task-123")
            self.assertEqual(send.call_args.args[0].get_header("Authorization"),"Token private-vidu")

    def test_imported_motion_is_local_and_survives_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/"example.mp4";source.write_bytes(b"fake-video-for-cache-test")
            cache=MotionCache(root);clip=cache.import_clip(source,"evening","kiss")
            self.assertEqual(MotionCache(root).get("evening","kiss"),clip)
            self.assertIsNone(cache.get("morning","kiss"))
            source=root/"bad.exe";source.write_bytes(b"test")
            with self.assertRaises(ValueError):cache.import_clip(source,"evening","kiss")


class DesktopLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def make_backend(self,folder):
        import os
        from desktop import Backend
        with patch.dict(os.environ,{"LISA_DATA_DIR":folder}):return Backend(self.app)

    def test_interruption_discards_a_late_chat_reply(self):
        with tempfile.TemporaryDirectory() as folder:
            backend=self.make_backend(folder);old=backend.generation;backend.stop()
            count=len(backend.messages)
            backend.finish_reply({"reply":"This late reply must not appear","mood":"smile"},old)
            self.assertEqual(len(backend.messages),count);backend.close()

    def test_voice_fallback_occurs_once_and_discloses_fish(self):
        with tempfile.TemporaryDirectory() as folder:
            backend=self.make_backend(folder);backend.store.settings.update(voice_provider="elevenlabs",voice_fallback=True,fish_voice_id="fake-id")
            backend.keys["fish"].session_key="fake-test-key-fish-12345"
            primary=MagicMock();primary.speech.side_effect=ApiError("ElevenLabs quota reached")
            fish=MagicMock();fish.speech.return_value=wav_from_pcm(b"\x00\x00"*500)
            def work(fn,callback):callback(fn())
            with patch.object(backend,"client",side_effect=lambda p:primary if p=="elevenlabs" else fish),patch.object(backend,"work",side_effect=work),patch.object(backend.audio,"play_wav"):
                backend.speak("Hello Sir","smile",backend.generation)
            primary.speech.assert_called_once();fish.speech.assert_called_once();self.assertIn("Fish fallback",backend.status);backend.close()

    def test_declined_action_does_not_execute(self):
        from PySide6.QtWidgets import QMessageBox
        with tempfile.TemporaryDirectory() as folder:
            backend=self.make_backend(folder)
            with patch("desktop.QMessageBox.question",return_value=QMessageBox.StandardButton.No),patch("desktop.open_target") as open_app:
                backend.review_action({"type":"open_app","value":"calculator"});open_app.assert_not_called()
            self.assertEqual(backend.messages[-1]["content"],"Action cancelled.");backend.close()

    def test_missing_transcription_key_never_opens_microphone(self):
        with tempfile.TemporaryDirectory() as folder:
            backend=self.make_backend(folder)
            with patch.object(backend.keys["groq"],"get",return_value=""),patch.object(backend.audio,"start_recording") as start:
                backend.mic();start.assert_not_called()
            backend.close();self.assertIsNone(backend.audio.input_stream)


if __name__=="__main__":unittest.main()
