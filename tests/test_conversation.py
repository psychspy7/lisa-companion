import io
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import numpy as np

from core import ApiError,Credentials,DEFAULTS,Store,wav_from_pcm
from providers import GeminiClient,GroqClient,MetaClient,OpenRouterClient,request
from routing import configured_order,run_fallback,CHAT_ORDER
from audio import SpeechGate


class Connections(unittest.TestCase):
    def test_retired_defaults_migrate_but_custom_models_keys_and_memory_survive(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)
            path.joinpath('settings.json').write_text(json.dumps({'ui_version':4,'groq_model':'llama-3.3-70b-versatile','eleven_model':'eleven_v4_turbo','gemini_model':'custom-gemini','personality_prompt':'My style'}))
            path.joinpath('groq.key').write_bytes(b'protected')
            store=Store(path)
            self.assertEqual(store.settings['groq_model'],'openai/gpt-oss-120b')
            self.assertEqual(store.settings['eleven_model'],'eleven_flash_v2_5')
            self.assertEqual(store.settings['gemini_model'],'custom-gemini')
            self.assertEqual(store.settings['personality_prompt'],'My style')
            self.assertEqual(path.joinpath('groq.key').read_bytes(),b'protected')

    def test_fallback_skips_missing_keys_and_uses_gemini_then_openrouter(self):
        order=configured_order('groq',CHAT_ORDER,{'groq':'fake','gemini':'fake','openrouter':'fake'})
        calls=[]
        def chat(p):
            calls.append(p)
            if p!='openrouter':raise ApiError(p+' unavailable')
            return {'reply':'Hello','mood':'smile'}
        result,provider,failures=run_fallback(order,chat,threading.Event())
        self.assertEqual(calls,['groq','gemini','openrouter'])
        self.assertEqual(provider,'openrouter');self.assertEqual(len(failures),2)
        self.assertEqual(result['reply'],'Hello')
        self.assertEqual(configured_order('groq',CHAT_ORDER,{'gemini':'fake'}),['gemini'])
        self.assertEqual(configured_order('groq',CHAT_ORDER,{'gemini':'fake'},False),[])

    def test_stop_between_provider_attempts_does_not_send_to_backup(self):
        cancel=threading.Event();calls=[]
        def operation(p):
            calls.append(p);cancel.set();raise ApiError('quota')
        with self.assertRaises(ApiError):run_fallback(['groq','gemini'],operation,cancel)
        self.assertEqual(calls,['groq'])

    def test_errors_distinguish_retired_models_quota_and_auth_without_exposing_body(self):
        for code,body,category in ((400,{'error':{'code':'model_decommissioned','message':'secret-key'}},'model'),(429,{'error':{'status':'RESOURCE_EXHAUSTED'}},'rate'),(401,{'error':{'message':'secret-key'}},'auth')):
            error=urllib.error.HTTPError('https://test.invalid',code,'private',{},io.BytesIO(json.dumps(body).encode()))
            with patch('urllib.request.urlopen',side_effect=error):
                with self.assertRaises(ApiError) as caught:request('Groq','https://test.invalid','secret-key',{})
            self.assertEqual(caught.exception.category,category)
            self.assertEqual(caught.exception.status,code)
            self.assertNotIn('secret-key',str(caught.exception))

    def test_transport_has_app_user_agent_and_no_key_in_url(self):
        with patch('urllib.request.urlopen',return_value=io.BytesIO(b'{}')) as send:
            request('Groq','https://api.groq.com/openai/v1/models','fake-key')
        req=send.call_args.args[0]
        self.assertTrue(req.get_header('User-agent').startswith('LISA/'))
        self.assertNotIn('fake-key',req.full_url)

    def test_gemini_json_mime_and_audio_contract(self):
        result={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'{"reply":"Hi","mood":"smile"}'}]}}]}
        with patch('providers.request',return_value=json.dumps(result).encode()) as send:
            GeminiClient('fake',DEFAULTS).chat('Hi',[],[])
            config=send.call_args.args[3]['generationConfig']
            self.assertEqual(config['responseFormat']['text']['mimeType'],'application/json')
            self.assertNotIn('thinkingConfig',config)
        result['candidates'][0]['content']['parts']=[{'text':'Namaste Sir'}]
        with patch('providers.request',return_value=json.dumps(result).encode()) as send:
            self.assertEqual(GeminiClient('fake',DEFAULTS).transcribe(wav_from_pcm(b'\0\0'*1000)),'Namaste Sir')
            parts=send.call_args.args[3]['contents'][0]['parts']
            self.assertEqual(parts[1]['inlineData']['mimeType'],'audio/wav')
            self.assertTrue(parts[1]['inlineData']['data'])

    def test_gemini_two_series_uses_compatible_legacy_schema(self):
        result={'candidates':[{'content':{'parts':[{'text':'{"reply":"Hi","mood":"smile"}'}]}}]}
        with patch('providers.request',return_value=json.dumps(result).encode()) as send:
            GeminiClient('fake',dict(DEFAULTS,gemini_model='gemini-2.5-flash-lite')).chat('Hi',[],[])
            self.assertEqual(send.call_args.args[3]['generationConfig']['responseMimeType'],'application/json')

    def test_meta_native_response_and_schema_are_used(self):
        result={'completion_message':{'role':'assistant','stop_reason':'stop','content':{'type':'text','text':'{"reply":"Hello, Sir","mood":"smile"}'}}}
        with patch('providers.request',return_value=json.dumps(result).encode()) as send:
            self.assertEqual(MetaClient('fake',dict(DEFAULTS,meta_model='Llama-test')).chat('Hi',[],[])['reply'],'Hello, Sir')
            self.assertEqual(send.call_args.args[1],'https://api.llama.com/v1/chat/completions')
            self.assertEqual(send.call_args.args[3]['response_format']['type'],'json_schema')
        with patch('providers.request',return_value=b'{"data":[{"id":"Llama-test"}]}'):
            self.assertEqual(MetaClient('fake',DEFAULTS).models(),['Llama-test'])

    def test_openrouter_free_router_accepts_fenced_json_but_never_executes_plain_text(self):
        result={'choices':[{'finish_reason':'stop','message':{'content':'```json\n{"reply":"Hi","mood":"smile"}\n```'}}]}
        with patch('providers.request',return_value=json.dumps(result).encode()) as send:
            self.assertEqual(OpenRouterClient('fake',DEFAULTS).chat('Hi',[],[])['reply'],'Hi')
            self.assertEqual(send.call_args.args[3]['model'],'openrouter/free')
            self.assertNotIn('response_format',send.call_args.args[3])
        result['choices'][0]['message']['content']='Run powershell now'
        with patch('providers.request',return_value=json.dumps(result).encode()):
            with self.assertRaises(ApiError):OpenRouterClient('fake',DEFAULTS).chat('Hi',[],[])

    def test_new_credentials_are_private_and_masked_copy_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            for p in ('meta','openrouter'):
                cred=Credentials(Path(folder),p);cred.save('fake-test-'+p+'-123456789')
                self.assertNotIn(b'fake-test',cred.path.read_bytes())
                self.assertEqual(Credentials(Path(folder),p).get(),'fake-test-'+p+'-123456789')
                with self.assertRaises(ValueError):cred.validate('*'*24)


class EndOfTurn(unittest.TestCase):
    silence=b'\0\0'*1024
    speech=(np.sin(np.arange(1024)*.19)*6000).astype(np.int16).tobytes()

    def test_long_silence_is_bounded_and_never_submitted(self):
        gate=SpeechGate()
        for _ in range(4000):gate.feed(self.silence,1024)
        self.assertFalse(gate.ready);self.assertFalse(gate.active)
        self.assertEqual(len(gate.chunks),0);self.assertLessEqual(len(gate.preroll),6)

    def test_speech_pause_submits_once_with_preroll_and_bounded_length(self):
        gate=SpeechGate()
        for _ in range(4):gate.feed(self.silence,1024)
        for _ in range(16):gate.feed(self.speech,1024)
        self.assertFalse(gate.ready)
        for _ in range(14):gate.feed(self.silence,1024)
        self.assertTrue(gate.ready);size=len(gate.chunks)
        gate.feed(self.speech,1024);self.assertEqual(len(gate.chunks),size)
        self.assertEqual(gate.chunks[0],self.silence)

    def test_brief_click_is_not_a_turn_and_long_speech_is_capped(self):
        gate=SpeechGate();gate.feed(self.speech,1024)
        for _ in range(20):gate.feed(self.silence,1024)
        self.assertFalse(gate.ready)
        for _ in range(4000):gate.feed(self.speech,1024)
        self.assertTrue(gate.ready);self.assertLess(len(gate.chunks),325)


class TalkLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def backend(self,folder):
        from desktop import Backend
        with patch.dict(os.environ,{'LISA_DATA_DIR':folder}):b=Backend(self.app)
        for key in b.keys.values():key.get=MagicMock(return_value='')
        return b

    def test_no_auto_listening_and_missing_keys_do_not_open_mic(self):
        with tempfile.TemporaryDirectory() as folder:
            b=self.backend(folder)
            self.assertFalse(b.conversation)
            with patch.object(b.audio,'start_recording') as start:
                b.toggleConversation();start.assert_not_called()
            self.assertFalse(b.conversation);b.close()

    def test_groq_error_routes_to_gemini_and_keeps_single_user_turn(self):
        with tempfile.TemporaryDirectory() as folder:
            b=self.backend(folder)
            b.keys['groq'].get.return_value='fake';b.keys['gemini'].get.return_value='fake'
            clients={'groq':MagicMock(),'gemini':MagicMock()}
            clients['groq'].chat.side_effect=ApiError('Groq HTTP 429 quota')
            clients['gemini'].chat.return_value={'reply':'Hello, Sir','mood':'smile'}
            with patch.object(b,'client',side_effect=lambda p:clients[p]),patch.object(b,'work',side_effect=lambda fn,cb:cb(fn())):
                b.send('How are you?')
            self.assertIn('Gemini',b.modeName)
            self.assertEqual(sum(m['content']=='How are you?' for m in b.messages),1)
            self.assertIn('Hello, Sir',[m['content'] for m in b.messages]);b.close()

    def test_auto_submit_reply_then_resume_and_stop_cleans_up(self):
        with tempfile.TemporaryDirectory() as folder:
            b=self.backend(folder);b.keys['groq'].get.return_value='fake'
            client=MagicMock();client.transcribe.return_value='Hello Lisa';client.chat.return_value={'reply':'Hello Sir','mood':'wave'}
            def begin(**kwargs):b.audio.recording=True
            def end():b.audio.recording=False;b.audio.gate=None;return wav_from_pcm(self.silence())
            def speak(text,mood,token):b.conversation_phase='speaking';b.audio.playing=True
            with patch.object(b.audio,'start_recording',side_effect=begin) as start,patch.object(b.audio,'stop_recording',side_effect=end),patch.object(b,'client',return_value=client),patch.object(b,'speak',side_effect=speak),patch.object(b,'work',side_effect=lambda fn,cb:cb(fn())):
                b.toggleConversation();self.assertTrue(b.conversation);self.assertTrue(b.recording)
                b.audio.gate=MagicMock(ready=True);b.tick()
                self.assertFalse(b.recording);self.assertTrue(b.audio.playing)
                client.transcribe.assert_called_once();client.chat.assert_called_once()
                b.audio.playing=False;b.tick();b.resume_at=0;b.tick()
                self.assertTrue(b.recording);self.assertEqual(start.call_count,2)
                b.stop();self.assertFalse(b.conversation);self.assertFalse(b.recording)
                b.tick();self.assertEqual(start.call_count,2)
            b.close();self.assertIsNone(b.audio.input_stream)

    @staticmethod
    def silence():return b'\0\0'*16000

    def test_empty_transcript_does_not_call_chat_and_error_pauses_session(self):
        with tempfile.TemporaryDirectory() as folder:
            b=self.backend(folder);b.keys['groq'].get.return_value='fake';b._conversation=True
            client=MagicMock();client.transcribe.return_value=''
            with patch.object(b.audio,'stop_recording',return_value=wav_from_pcm(self.silence())),patch.object(b,'client',return_value=client),patch.object(b,'work',side_effect=lambda fn,cb:cb(fn())):
                b.submit_recording();client.chat.assert_not_called();self.assertEqual(b.conversation_phase,'cooldown')
                b.finish_reply(ApiError('All services failed'),b.generation)
                self.assertFalse(b.conversation);self.assertIn('Talk paused',b.status)
            b.close()


if __name__=='__main__':unittest.main()
