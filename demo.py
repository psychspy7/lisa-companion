"""Clearly labelled free offline preview. Preset replies, not a language model."""
from pathlib import Path
import subprocess
import tempfile
import threading

_lock=threading.Lock()
_process=None


def cancel():
    global _process
    with _lock:
        process=_process
    if process and process.poll() is None:
        process.terminate()


def reply(text,memories):
    message=text.casefold()
    if any(word in message for word in ('sad','cry','upset','lonely','bad day','dukh','udaas')):
        return {'reply':"I’m here, Sir. We can take it slowly. Want to tell me what made today hard?",'mood':'caring'}
    if any(word in message for word in ('kiss','love','cute','pretty','beautiful')):
        return {'reply':"A little flying kiss for you, Sir. You’re making me blush.",'mood':'kiss'}
    if any(word in message for word in ('command','dominat','boss','motivat','work','study')):
        return {'reply':"Alright, Sir. Shoulders back, water nearby, and one tiny task first. I’m cheering for you.",'mood':'commanding'}
    if any(word in message for word in ('tea','chai','coffee')):
        return {'reply':"Chai break, Sir? You handle the real cup; I’ll handle the company.",'mood':'tea'}
    if any(word in message for word in ('angry','mad','roast')):
        return {'reply':"Sir, your procrastination has more sequels than a movie franchise. One little task and I’ll stop teasing.",'mood':'teasing'}
    if any(word in message for word in ('sleep','night','bed','neend')):
        return {'reply':"Goodnight, Sir. Put the day down for a while. I’ll be here when you open Lisa again.",'mood':'goodnight'}
    if any(word in message for word in ('sit','sitting')):
        return {'reply':"Let’s sit for a moment, Sir. No rush.",'mood':'sitting'}
    if any(word in message for word in ('hi','hello','namaste','kaisi','kaise')):
        return {'reply':"Hi, Sir! Main yahin hoon. Tell me about your day.",'mood':'wave'}
    if 'remember' in message and memories:
        return {'reply':"You saved this note for me, Sir: "+memories[-1],'mood':'listening'}
    return {'reply':"You have my attention, Sir. This free preview uses preset replies—try asking for tea, a kiss, motivation, or a goodnight.",'mood':'smile'}


def speech(text,directory,cancel_event=None):
    """Use installed Windows voice without API charges; no new software."""
    with tempfile.TemporaryDirectory(prefix='demo-voice-',dir=directory) as folder:
        path=Path(folder)
        (path/'text.txt').write_text(text,encoding='utf-8-sig')
        def quote(value): return "'"+str(value).replace("'","''")+"'"
        script=path/'speak.ps1'
        script.write_text("Add-Type -AssemblyName System.Speech\n"+
            "$lisaSynth = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"+
            "$lisaFemale = $lisaSynth.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Gender -eq 'Female' -and $_.Enabled } | Select-Object -First 1\n"+
            "if ($lisaFemale) { $lisaSynth.SelectVoice($lisaFemale.VoiceInfo.Name) }\n"+
            "$lisaSynth.SetOutputToWaveFile("+quote(path/'voice.wav')+")\n"+
            "$lisaText = [System.IO.File]::ReadAllText("+quote(path/'text.txt')+")\n"+
            "try { $lisaSynth.Speak($lisaText) } finally { $lisaSynth.Dispose() }\n",encoding='utf-8-sig')
        global _process
        process=None
        try:
            if cancel_event and cancel_event.is_set(): return b''
            process=subprocess.Popen(['powershell.exe','-NoProfile','-WindowStyle','Hidden','-File',str(script)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
            with _lock: _process=process
            for _ in range(300):
                if cancel_event and cancel_event.is_set():
                    process.terminate()
                    process.wait(timeout=5)
                    return b''
                try:
                    process.wait(timeout=.1)
                    break
                except subprocess.TimeoutExpired:
                    continue
            else:
                process.terminate()
                process.wait(timeout=5)
                raise RuntimeError()
            if process.returncode!=0: raise RuntimeError()
            return (path/'voice.wav').read_bytes()
        except Exception:
            raise RuntimeError('Free Windows voice is unavailable. Turn Lisa’s voice off, or use OpenAI mode.') from None
        finally:
            with _lock:
                if _process is process: _process=None
