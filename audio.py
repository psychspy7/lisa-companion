"""Explicit microphone lifetime and interruptible audio. No background listener."""
import io
import math
import threading
import wave
from collections import deque
import numpy as np
import sounddevice as sd
from core import wav_from_pcm


class SpeechGate:
    """Energy-based end-of-turn detection with bounded silence and a pre-roll."""
    def __init__(self,threshold=.018,pause=.85,rate=16000):
        self.threshold=max(.003,min(.15,float(threshold)))
        self.pause=max(.45,min(2.5,float(pause)));self.rate=rate
        self.preroll=deque(maxlen=6);self.chunks=[]
        self.active=False;self.ready=False;self.voiced=0.;self.silence=0.;self.elapsed=0.;self.level=0.

    def feed(self,data,frames):
        if self.ready:return
        samples=np.frombuffer(data,dtype=np.int16).astype(np.float32)/32768
        self.level=float(np.sqrt(np.mean(samples*samples))) if samples.size else 0.
        duration=frames/self.rate;voice=self.level>=self.threshold
        if not self.active:
            self.preroll.append(data)
            self.voiced=self.voiced+duration if voice else 0.
            if self.voiced>=.18:
                self.active=True;self.chunks=list(self.preroll);self.preroll.clear();self.elapsed=self.voiced
            return
        self.chunks.append(data);self.elapsed+=duration
        if voice:self.voiced+=duration;self.silence=0.
        else:self.silence+=duration
        if self.elapsed>=20 or self.silence>=self.pause:
            if self.voiced>=.25:self.ready=True
            else:
                self.active=False;self.chunks=[];self.voiced=self.silence=self.elapsed=0.


class Audio:
    def __init__(self):
        self.input_stream = None
        self.output_stream = None
        self.chunks = []
        self.frames = 0
        self.level = 0.0
        self.recording = False
        self.playing = False
        self.lock = threading.RLock()
        self.gate = None
        self.input_level = 0.0

    def start_recording(self,continuous=False,threshold=.018,pause=.85):
        if self.input_stream:self.stop_recording()
        self.stop_playback()
        self.chunks = []
        self.frames = 0
        self.recording = True
        self.gate = SpeechGate(threshold,pause) if continuous else None
        self.input_level=0.

        def collect(data, frames, time_info, status):
            with self.lock:
                if not self.recording:return
                if self.gate:
                    self.gate.feed(bytes(data),frames);self.input_level=self.gate.level
                elif self.frames < 16000 * 30:
                    self.chunks.append(bytes(data));self.frames += frames

        try:
            self.input_stream = sd.RawInputStream(samplerate=16000, channels=1, dtype="int16", callback=collect, blocksize=1024)
            self.input_stream.start()
        except Exception:
            self.recording = False
            if self.input_stream:
                self.input_stream.close()
            self.input_stream = None
            raise RuntimeError("Microphone unavailable. Check Windows microphone permission and your input device.") from None

    def stop_recording(self):
        self.recording = False
        if self.input_stream:
            stream,self.input_stream=self.input_stream,None
            try:
                stream.stop()
            except Exception:
                pass
            finally:
                try: stream.close()
                except Exception: pass
        with self.lock:
            pcm=b"".join(self.gate.chunks if self.gate else self.chunks)
            wav=wav_from_pcm(pcm)
            self.gate=None;self.input_level=0.
            self.chunks.clear();self.frames=0
        return wav

    @property
    def utterance_ready(self):
        with self.lock:return bool(self.gate and self.gate.ready)

    def stop_playback(self):
        with self.lock:
            self.playing = False
            self.level = 0.0
            stream, self.output_stream = self.output_stream, None
            if stream:
                try:
                    stream.abort()
                    stream.close()
                except Exception:
                    pass

    def play_wav(self, data, volume=0.75):
        with wave.open(io.BytesIO(data), "rb") as reader:
            width, channels, rate = reader.getsampwidth(), reader.getnchannels(), reader.getframerate()
            if width != 2:
                raise RuntimeError("Unsupported speech audio format.")
            samples = np.frombuffer(reader.readframes(reader.getnframes()), dtype=np.int16).reshape(-1, channels).astype(np.float32) / 32768.0
        self.play_samples(samples * volume, rate)

    def play_samples(self, samples, rate):
        self.stop_playback()
        cursor = 0
        self.playing = True

        def callback(output, frames, time_info, status):
            nonlocal cursor
            count = min(frames, len(samples) - cursor)
            output[:] = 0
            if count > 0 and self.playing:
                output[:count] = samples[cursor:cursor + count]
                self.level = min(1.0, float(np.sqrt(np.mean(output[:count] ** 2))) * 8.0)
                cursor += count
            if count < frames or not self.playing:
                self.playing = False
                self.level = 0.0
                raise sd.CallbackStop

        with self.lock:
            try:
                self.output_stream = sd.OutputStream(samplerate=rate, channels=samples.shape[1], callback=callback, blocksize=1024)
                self.output_stream.start()
            except Exception:
                self.playing = False
                self.level = 0.0
                if self.output_stream:
                    try:
                        self.output_stream.close()
                    except Exception:
                        pass
                    self.output_stream = None
                raise RuntimeError("Audio output unavailable. Check your speakers or turn voice off.") from None

    def chime(self):
        if self.playing or self.recording:
            return
        rate = 22050
        t = np.arange(int(rate * 0.10)) / rate
        envelope = np.sin(np.pi * t / 0.10) ** 2
        samples = (np.sin(2 * np.pi * 660 * t) + 0.5 * np.sin(2 * np.pi * 990 * t)) * envelope * 0.035
        try:
            self.play_samples(samples.astype(np.float32).reshape(-1, 1), rate)
        except Exception:
            pass

    def close(self):
        self.stop_playback()
        if self.input_stream:
            self.stop_recording()
        self.chunks.clear()
