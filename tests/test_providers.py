import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import wave

from core import ApiError, Credentials, DEFAULTS, Store, dpapi, wav_from_pcm
from providers import GeminiClient, ElevenLabsClient, request


class ProviderIntegration(unittest.TestCase):
    def test_keys_are_separate_encrypted_and_survive_reload(self):
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder)
            for provider in ("gemini","elevenlabs"):
                fake="fake-test-key-"+provider+"-123456789"
                credential=Credentials(directory,provider)
                credential.save(fake)
                self.assertNotIn(fake.encode(),credential.path.read_bytes())
                self.assertEqual(Credentials(directory,provider).get(),fake)
                self.assertEqual(dpapi(credential.path.read_bytes(),True).decode(),fake)
            Credentials(directory,"gemini").forget()
            self.assertTrue((directory/"elevenlabs.key").exists())
            self.assertFalse((directory/"gemini.key").exists())

    def test_old_settings_and_saved_memory_migrate_without_openai_use(self):
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder)
            (directory/"settings.json").write_text(json.dumps({"model":"gpt-4o-mini","demo_enabled":False,"save_history":True}))
            (directory/"memories.json").write_text('["Sir likes tea"]')
            (directory/"history.json").write_text('[{"role":"user","content":"Hi"}]')
            store=Store(directory)
            self.assertEqual(store.memories,["Sir likes tea"])
            self.assertTrue(store.history)
            self.assertTrue(store.settings["gemini_model"].startswith("gemini-"))
            self.assertFalse(store.settings["demo_enabled"])

    def test_chat_routes_key_in_header_and_preserves_personality_context(self):
        client=GeminiClient("fake-gemini-secret",DEFAULTS)
        response={"candidates":[{"finishReason":"STOP","content":{"parts":[{"text":json.dumps({"reply":"Hello, Sir.","mood":"smile"})}]}}]}
        with patch("urllib.request.urlopen",return_value=io.BytesIO(json.dumps(response).encode())) as open_url:
            answer=client.chat("Namaste",[{"role":"user","content":"Hi"},{"role":"assistant","content":"Hello"}],["Sir prefers chai"])
            req=open_url.call_args.args[0]
            self.assertTrue(req.full_url.startswith("https://generativelanguage.googleapis.com/"))
            self.assertNotIn("secret",req.full_url)
            self.assertEqual(req.get_header("X-goog-api-key"),"fake-gemini-secret")
            body=json.loads(req.data)
            instructions=body["systemInstruction"]["parts"][0]["text"]
            self.assertIn("Sir prefers chai",instructions)
            self.assertIn("soft, warm, playful",instructions)
            self.assertEqual([c["role"] for c in body["contents"]],["user","model","user"])
            self.assertEqual(answer,{"reply":"Hello, Sir.","mood":"smile"})

    def test_blocked_or_incomplete_replies_do_not_become_speech(self):
        client=GeminiClient("fake",DEFAULTS)
        replies=[{}, {"candidates":[{"finishReason":"SAFETY"}]}, {"candidates":[{"finishReason":"MAX_TOKENS"}]}, {"candidates":[{"content":{"parts":[{"text":'{"reply":"Hi", "mood":"unknown"}'}]}}]}]
        for response in replies:
            with self.subTest(response=response), patch("providers.request",return_value=json.dumps(response).encode()):
                with self.assertRaises(ApiError): client.chat("Hello",[],[])

    def test_eleven_speech_uses_chosen_voice_and_playable_audio(self):
        settings=dict(DEFAULTS,eleven_voice_id="voice-test-123",eleven_model="eleven_multilingual_v2")
        client=ElevenLabsClient("fake-eleven-key",settings)
        with patch("providers.request",return_value=b"\x00\x00"*240) as send:
            wav=client.speech("Hello, Sir.")
            self.assertIn("/voice-test-123?output_format=pcm_24000",send.call_args.args[1])
            self.assertEqual(send.call_args.args[3]["text"],"Hello, Sir.")
            with wave.open(io.BytesIO(wav)) as reader:
                self.assertEqual((reader.getframerate(),reader.getsampwidth(),reader.getnchannels()),(24000,2,1))
        with patch("providers.request") as send:
            with self.assertRaises(ApiError): ElevenLabsClient("fake",DEFAULTS).speech("Hello")
            send.assert_not_called()

    def test_recording_transcribes_via_elevenlabs_not_gemini(self):
        client=ElevenLabsClient("fake",dict(DEFAULTS,language="Hinglish"))
        wav=wav_from_pcm(b"\x00\x00"*8000)
        with patch("providers.request",return_value=b'{"text":"Hello Sir"}') as send:
            self.assertEqual(client.transcribe(wav),"Hello Sir")
            self.assertEqual(send.call_args.args[1],"https://api.elevenlabs.io/v1/speech-to-text")
            body=send.call_args.args[3]
            self.assertIn(wav,body)
            self.assertIn(b"scribe_v2",body)
            self.assertNotIn(b"language_code",body)
            self.assertIn(b"tag_audio_events",body)

    def test_service_errors_are_safe_and_no_automatic_retry_spends_quota(self):
        for code in (400,401,403,404,422,429,500):
            for provider in ("Gemini","ElevenLabs"):
                error=urllib.error.HTTPError("https://provider.invalid",code,"secret key in message",{},io.BytesIO(b"secret body"))
                with self.subTest(code=code,provider=provider), patch("urllib.request.urlopen",side_effect=error) as send:
                    with self.assertRaises(ApiError) as context: request(provider,"https://provider.invalid","secret-key",{})
                    self.assertNotIn("secret",str(context.exception))
                    self.assertIn(provider,str(context.exception))
                    send.assert_called_once()

    def test_voice_listing_and_optional_chime_share_only_elevenlabs_key(self):
        client=ElevenLabsClient("fake",DEFAULTS)
        with patch("providers.request",return_value=b'{"voices":[{"name":"Lisa voice","voice_id":"example"}]}') as send:
            self.assertEqual(client.voices(),[{"name":"Lisa voice","voice_id":"example"}])
            self.assertIn("/v2/voices?",send.call_args.args[1])
        with patch("providers.request",return_value=b"\x00\x00"*240) as send:
            self.assertTrue(client.sound_effect().startswith(b"RIFF"))
            self.assertEqual(send.call_args.args[3]["duration_seconds"],0.5)


if __name__=="__main__": unittest.main()
