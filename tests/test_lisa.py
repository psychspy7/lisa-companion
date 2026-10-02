import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import urllib.error

from core import Store, Credentials, DEFAULTS, OpenAIClient, ApiError, dpapi
from audio import Audio
import updates


class SafetyAndLifecycle(unittest.TestCase):
    def test_history_is_opt_in_and_memory_persists(self):
        with tempfile.TemporaryDirectory() as folder:
            store=Store(Path(folder))
            store.history=[{"role":"user","content":"private conversation"}]
            store.add_memory("Sir prefers tea")
            self.assertFalse((Path(folder)/"history.json").exists())
            self.assertEqual(Store(Path(folder)).memories,["Sir prefers tea"])
            store.settings["save_history"]=True
            store.save()
            self.assertEqual(Store(Path(folder)).history,store.history)
            store.settings["save_history"]=False
            store.save()
            self.assertFalse((Path(folder)/"history.json").exists())

    def test_windows_key_storage_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            credentials=Credentials(Path(folder))
            fake="sk-test-THIS-IS-NOT-A-REAL-KEY"
            credentials.save(fake)
            self.assertNotIn(fake.encode(),credentials.path.read_bytes())
            self.assertEqual(dpapi(credentials.path.read_bytes(),True).decode(),fake)
            credentials.forget()
            self.assertFalse(credentials.path.exists())

    def test_closing_releases_input_and_output(self):
        audio=Audio()
        self.assertIsNone(audio.input_stream)
        input_stream=MagicMock()
        output_stream=MagicMock()
        audio.input_stream=input_stream
        audio.output_stream=output_stream
        audio.recording=audio.playing=True
        audio.chunks=[b"\x00\x00"*200]
        audio.close()
        input_stream.stop.assert_called_once()
        input_stream.close.assert_called_once()
        output_stream.abort.assert_called_once()
        output_stream.close.assert_called_once()
        self.assertIsNone(audio.input_stream)
        self.assertIsNone(audio.output_stream)
        self.assertFalse(audio.recording)
        self.assertFalse(audio.playing)
        self.assertEqual(audio.chunks,[])

    def test_chat_request_and_refusal(self):
        client=OpenAIClient("sk-fake",DEFAULTS)
        response={"output":[{"content":[{"type":"output_text","text":json.dumps({"reply":"Hello, Sir.","mood":"smile"})}]}]}
        with patch.object(client,"request",return_value=json.dumps(response).encode()) as request:
            self.assertEqual(client.chat("Hi",[],["Likes tea"])["mood"],"smile")
            body=request.call_args.args[1]
            self.assertFalse(body["store"])
            self.assertEqual(body["input"],[{"role":"user","content":"Hi"}])
            self.assertIn("Likes tea",body["instructions"])
        with patch.object(client,"request",return_value=b'{"output":[{"content":[{"type":"refusal"}]}]}'):
            with self.assertRaises(ApiError): client.chat("Hi",[],[])

    def test_http_errors_do_not_echo_key_or_body(self):
        client=OpenAIClient("sk-fake-secret",DEFAULTS)
        err=urllib.error.HTTPError("https://api.openai.com/v1/responses",401,"bad",{},io.BytesIO(b"sk-fake-secret"))
        with patch("urllib.request.urlopen",side_effect=err):
            with self.assertRaises(ApiError) as context: client.request("responses",{})
            self.assertNotIn("sk-fake",str(context.exception))

    def test_updates_verify_hash_and_discard_tampered_download(self):
        info={"repository":"psychspy7/lisa-companion","exe":"https://github.com/psychspy7/lisa-companion/releases/download/v0.2.0/LISA.exe","checksum":"https://github.com/psychspy7/lisa-companion/releases/download/v0.2.0/SHA256SUMS.txt"}
        payload=b"test executable content"
        checksum=(hashlib.sha256(payload).hexdigest()+"  LISA.exe\n").encode()
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)
            with patch("urllib.request.urlopen",side_effect=[io.BytesIO(checksum),io.BytesIO(payload)]):
                self.assertEqual(updates.download_release(info,path).read_bytes(),payload)
            with patch("urllib.request.urlopen",side_effect=[io.BytesIO(checksum),io.BytesIO(b"tampered")]):
                with self.assertRaisesRegex(RuntimeError,"checksum did not match"): updates.download_release(info,path)
            self.assertFalse((path/"LISA-new.exe").exists())
            info["exe"]="https://example.com/untrusted.exe"
            with self.assertRaisesRegex(RuntimeError,"not from"): updates.download_release(info,path)


if __name__=="__main__": unittest.main()
