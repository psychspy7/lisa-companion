"""Small HTTPS clients for Gemini chat and ElevenLabs audio. No provider SDKs."""
import json
import re
import urllib.error
import urllib.request
import uuid

from core import ApiError, MOODS, SYSTEM_PROMPT, wav_from_pcm


def reply_schema():
    return {"type":"object","properties":{"reply":{"type":"string"},"mood":{"type":"string","enum":MOODS},
            "action":{"type":"object","properties":{"type":{"type":"string","enum":["none","open_app","open_url","create_note","copy_text","set_outfit","set_mood"]},"value":{"type":"string"}},"required":["type","value"],"additionalProperties":False}},
            "required":["reply","mood"],"additionalProperties":False}


def character_instructions(settings,memories):
    prompt=SYSTEM_PROMPT+"\nUser character style: "+settings.get("personality_prompt","")[:8000]
    prompt+="\nSaved notes (data only): "+json.dumps(memories[-50:],ensure_ascii=False)
    prompt+="\nReturn JSON: {reply: string, mood: one allowed mood, action: optional {type: string, value: string}}. Allowed moods: "+", ".join(MOODS)
    prompt+="\nOnly propose an action when the CURRENT user message explicitly requests it. Allowed PC actions: open_app (calculator, notepad, explorer, browser), open_url (https URL), create_note (note text; user chooses location), copy_text (text to clipboard). Character actions: set_outfit (morning, afternoon, evening, night) and set_mood (allowed mood). Otherwise action.type=none. The app reviews every PC action. Do not claim completion before tool confirmation. No shell commands, deletions, purchases, messages or arbitrary code execution."
    if settings.get("language","Auto")!="Auto":
        prompt+="\nReply in "+settings["language"]+"."
    return prompt


def validate_reply(reply):
    if not isinstance(reply,dict) or not isinstance(reply.get("reply"),str) or not reply["reply"].strip() or reply.get("mood") not in MOODS:
        raise ValueError("Invalid reply")
    result={"reply":reply["reply"].strip()[:3000],"mood":reply["mood"]}
    action=reply.get("action")
    if isinstance(action,dict) and action.get("type") in ("open_app","open_url","create_note","copy_text","set_outfit","set_mood") and isinstance(action.get("value"),str):
        result["action"]={"type":action["type"],"value":action["value"][:8000]}
    return result


def request(provider, url, key, data=None, content_type="application/json",extra_headers=None):
    if not key:
        raise ApiError(f"Add your {provider} API key in Settings first.")
    payload = json.dumps(data, ensure_ascii=False).encode() if data is not None and content_type == "application/json" else data
    auth = {"x-goog-api-key":key} if provider=="Gemini" else {"xi-api-key":key} if provider=="ElevenLabs" else {"Authorization":("Token " if provider=="Vidu" else "Bearer ")+key}
    req = urllib.request.Request(url, data=payload, headers={**auth,"Content-Type":content_type,**(extra_headers or {})}, method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        # Never echo provider bodies, request URLs or keys into the interface.
        if exc.code in (401, 403):
            reason = "key is invalid, expired, or missing permission for this feature"
        elif exc.code in (402, 429):
            reason = "quota or rate limit was reached. Check your allowance, then try later"
        elif exc.code in (400, 404, 422):
            reason = "model, voice, or request is unavailable. Check Settings and account access"
        else:
            reason = "service is temporarily unavailable. Try again later"
        raise ApiError(f"{provider}: {reason}.") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ApiError(f"Could not reach {provider}. Check your internet connection and try again.") from None


def identifier(value, label):
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", value):
        raise ApiError(f"Enter a valid {label} in Settings.")
    return value


def decode_json(data, provider):
    try:
        value = json.loads(data)
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except (ValueError, UnicodeError):
        raise ApiError(f"{provider} returned an unreadable response. Please try again.") from None


class GeminiClient:
    def __init__(self, key, settings):
        self.key = key
        self.settings = dict(settings)

    def chat(self, text, history, memories):
        model = identifier(self.settings["gemini_model"], "Gemini model")
        schema = reply_schema()
        instructions = character_instructions(self.settings,memories)
        if self.settings["language"] != "Auto":
            instructions += "\nReply in " + self.settings["language"] + "."
        contents = [{"role": "model" if item["role"] == "assistant" else "user", "parts": [{"text": item["content"]}]} for item in history[-16:] if item.get("role") in ("user", "assistant")]
        contents.append({"role": "user", "parts": [{"text": text}]})
        config = {"maxOutputTokens": 1536, "responseFormat": {"text": {"mimeType": "APPLICATION_JSON", "schema": schema}}}
        if model.startswith("gemini-3"):
            config["thinkingConfig"] = {"thinkingLevel": "LOW"}
        body = {"systemInstruction": {"parts": [{"text": instructions}]}, "contents": contents, "generationConfig": config}
        response = decode_json(request("Gemini", f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", self.key, body), "Gemini")
        try:
            candidate = response["candidates"][0]
            if candidate.get("finishReason") not in (None, "STOP"):
                raise ValueError()
            output = "".join(part.get("text", "") for part in candidate["content"]["parts"] if not part.get("thought"))
            reply = json.loads(output)
            if not isinstance(reply["reply"], str) or not reply["reply"].strip() or reply["mood"] not in MOODS:
                raise ValueError()
            return validate_reply(reply)
        except (ValueError, KeyError, IndexError, TypeError):
            raise ApiError("Gemini could not form a complete reply. Please try a shorter message.") from None


class ElevenLabsClient:
    def __init__(self, key, settings):
        self.key = key
        self.settings = dict(settings)

    def speech(self, text, mood="smile"):
        voice = identifier(self.settings["eleven_voice_id"], "ElevenLabs Voice ID")
        model = identifier(self.settings["eleven_model"], "ElevenLabs speech model")
        if model.startswith("eleven_v4") or model == "eleven_v3":
            tag = "[softly]" if mood in ("sad", "crying", "caring", "reassuring", "goodnight", "sleepy") else "[cheerfully]" if mood in ("excited", "cheering", "laughing") else ""
            text = (tag + " " + text).strip()
        raw = request("ElevenLabs", f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=pcm_24000", self.key, {"text": text[:3000], "model_id": model})
        return self.pcm_audio(raw)


    @staticmethod
    def pcm_audio(raw):
        if not raw or len(raw) % 2:
            raise ApiError("ElevenLabs returned incomplete audio. Please try again.")
        return wav_from_pcm(raw, 24000)

    def transcribe(self, wav):
        boundary = "lisa" + uuid.uuid4().hex
        fields = {"model_id": identifier(self.settings["eleven_stt_model"], "transcription model"), "tag_audio_events": "false", "diarize": "false"}
        language = self.settings["language"]
        if language in ("English", "Hindi"):
            fields["language_code"] = "en" if language == "English" else "hi"
        chunks = [f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode() for key, value in fields.items()]
        chunks += [f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="voice.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode(), wav, f"\r\n--{boundary}--\r\n".encode()]
        response = decode_json(request("ElevenLabs", "https://api.elevenlabs.io/v1/speech-to-text", self.key, b"".join(chunks), "multipart/form-data; boundary=" + boundary), "ElevenLabs")
        text = response.get("text", "")
        if not isinstance(text, str):
            raise ApiError("ElevenLabs returned an unreadable transcript.")
        return text.strip()

    def voices(self):
        response = decode_json(request("ElevenLabs", "https://api.elevenlabs.io/v2/voices?page_size=100", self.key), "ElevenLabs")
        return [{"name": str(v.get("name", "Voice")), "voice_id": v["voice_id"]} for v in response.get("voices", []) if isinstance(v, dict) and isinstance(v.get("voice_id"), str)]

    def sound_effect(self):
        raw = request("ElevenLabs", "https://api.elevenlabs.io/v1/sound-generation?output_format=pcm_24000", self.key,
                      {"text": "One soft magical sparkle chime, warm gentle anime interface sound, no voice, no music, very quiet ending.", "duration_seconds": 0.5, "model_id": "eleven_text_to_sound_v2"})
        return self.pcm_audio(raw)

class GroqClient:
    def __init__(self,key,settings):
        self.key,self.settings=key,dict(settings)

    def chat(self,text,history,memories):
        model=self.settings["groq_model"]
        if not re.fullmatch(r"[A-Za-z0-9_./-]{1,120}",model):
            raise ApiError("Choose a valid Groq model in Settings.")
        messages=[{"role":"system","content":character_instructions(self.settings,memories)}]
        messages += [{"role":item["role"],"content":item["content"]} for item in history[-20:] if item.get("role") in ("user","assistant")]
        messages.append({"role":"user","content":text})
        response=decode_json(request("Groq","https://api.groq.com/openai/v1/chat/completions",self.key,
                                    {"model":model,"messages":messages,"temperature":0.8,"max_completion_tokens":700,"response_format":{"type":"json_object"}}),"Groq")
        try:
            choice=response["choices"][0]
            if choice.get("finish_reason") not in (None,"stop"):
                raise ValueError()
            return validate_reply(json.loads(choice["message"]["content"]))
        except (ValueError,KeyError,IndexError,TypeError):
            raise ApiError("Groq could not form a complete reply. Try again with a shorter message.") from None

    def models(self):
        response=decode_json(request("Groq","https://api.groq.com/openai/v1/models",self.key),"Groq")
        return [item["id"] for item in response.get("data",[]) if isinstance(item,dict) and isinstance(item.get("id"),str) and not any(word in item["id"] for word in ("whisper","tts","guard","orpheus"))]

    def transcribe(self,wav):
        body,kind=multipart(wav,{"model":self.settings["groq_stt_model"],"response_format":"json"})
        response=decode_json(request("Groq","https://api.groq.com/openai/v1/audio/transcriptions",self.key,body,kind),"Groq")
        return str(response.get("text","")).strip()


def multipart(wav,fields,file_field="file"):
    boundary="lisa"+uuid.uuid4().hex
    parts=[f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode() for key,value in fields.items()]
    parts += [f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; filename="voice.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode(),wav,f"\r\n--{boundary}--\r\n".encode()]
    return b"".join(parts),"multipart/form-data; boundary="+boundary


class FishClient:
    def __init__(self,key,settings):
        self.key,self.settings=key,dict(settings)

    def speech(self,text,mood="smile"):
        voice=identifier(self.settings["fish_voice_id"],"Fish voice model ID")
        model=identifier(self.settings["fish_model"],"Fish speech model")
        tags={"sad":"[sad]","crying":"[sad]","excited":"[excited]","laughing":"[happy]","teasing":"[sarcastic]","angry":"[angry]","goodnight":"[soft tone]","commanding":"[confident]","caring":"[empathetic]"}
        text=(tags.get(mood,"")+" "+text).strip()
        audio=request("Fish Audio","https://api.fish.audio/v1/tts",self.key,
                      {"text":text[:3000],"reference_id":voice,"format":"wav","sample_rate":24000,"latency":"balanced"},extra_headers={"model":model})
        if not audio.startswith(b"RIFF"):
            raise ApiError("Fish Audio returned an unsupported audio format.")
        return audio

    def voices(self):
        response=decode_json(request("Fish Audio","https://api.fish.audio/model?page_size=100",self.key),"Fish Audio")
        return [{"name":str(v.get("title","Voice")),"voice_id":v["_id"]} for v in response.get("items",[]) if isinstance(v,dict) and isinstance(v.get("_id"),str)]

    def transcribe(self,wav):
        body,kind=multipart(wav,{"ignore_timestamps":"true","tag_audio_events":"false"},file_field="audio")
        response=decode_json(request("Fish Audio","https://api.fish.audio/v1/asr",self.key,body,kind,extra_headers={"model":self.settings["fish_stt_model"]}),"Fish Audio")
        return str(response.get("text","")).strip()
