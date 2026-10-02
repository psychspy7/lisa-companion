# LISA

Source and Windows releases: https://github.com/psychspy7/lisa-companion

A standalone Windows companion app starring Lisa: a clearly adult fictional anime character with midnight-blue hair, lavender tips, blue eyes, cat-ear accessories, and a warm, playful personality. She naturally calls you **Sir**.

## Try the test build

Open **LISA.exe** on Windows 10 or 11, 64-bit. No Python installation is needed. Close the window to quit completely. Lisa has no tray process, startup service, camera access, or background microphone listener.

The first launch uses **Free demo**, which has clearly labelled preset replies and your installed Windows voice. Try “chai”, “kiss”, “sit”, “motivate me”, “I am sad”, or “goodnight”. Turn on **Lisa’s voice** for spoken replies. Free demo is a visual and interaction preview, not a language model. It cannot transcribe voice input.

For real conversation, open **Settings → Chat & voice** and enter your **Gemini API key** and **ElevenLabs API key**. Click **Test chat**, **Load voices**, choose a voice, and **Preview voice**. You can also enter a Voice ID directly. Click **Save & use AI**, then turn on **Lisa’s voice** in the main window. Text chat only needs Gemini; listening and speaking use ElevenLabs. No OpenAI key is needed for this version. Blank key fields keep existing keys. New keys are encrypted for your Windows account, separately for each provider. Enter secrets inside Settings, never in a chat message or public repository.

Internet and provider allowance are required. Gemini free-tier limits and ElevenLabs feature access depend on your account. A restricted ElevenLabs key needs access to text-to-speech, speech-to-text, and voices; sound effects permission is only needed for the optional chime. Replace expired keys in Settings. Tests/previews make real requests using your allowance; the app never retries quota errors automatically. Live service verification must be completed with your own keys. This release was checked with mocked provider responses because the supplied screenshots conceal the credentials.

**Talk** opens the microphone only when pressed in AI mode with both keys available. Press **Finish talking** to submit the recording, or **Stop/Escape** to discard it. Recording is limited to 30 seconds. Talk and Stop interrupt Lisa’s speech, and late network results are discarded after interruption. Closing the app releases audio streams and exits the process. Submitted voice recordings go to ElevenLabs for transcription. Chat text, transcribed text, recent conversation and your saved notes go to Gemini. Lisa’s reply text goes to ElevenLabs when voice is enabled. Recordings are not saved to disk. Providers may retain requests under their account policies; local history being off does not change provider retention. Camera stays off.

## Included in 0.2.0

- Four coordinated outfits for morning, afternoon, evening and night; selection by local PC time or manually.
- 36 illustrated poses: smile, shy, tea, sitting, wave, yawn, stretch, thinking, listening, commanding, angry, smirk, excited, laughing, surprised, proud, cheering, teasing, kiss, affectionate, elegant sitting, thumbs up, blushing, welcoming, apologetic, reassuring, peace, crying, sad, sleepy, goodnight, caring, pensive, self hug, cozy sitting and peaceful.
- Breathing/sway, software blinks on suitable unobscured faces, and audio-level mouth movement. Poses change as illustrations. This is a sprite prototype, not a fully rigged Live2D or 3D model. Some expressions already have closed eyes or covered mouths and suppress facial overlays.
- Gemini chat and ElevenLabs speech/transcription for English, Hindi and Hinglish, with editable models, a voice selector and connection tests.
- Optional long-term notes in **Memory**, with add/remove controls. Chat history is off by default and optional in Settings.
- Local Windows DPAPI encryption for keys entered in Settings. No API key, personal memory or conversation is bundled.
- Soft UI chimes, configurable motion and sound, and an update button. Optionally generate one short ElevenLabs chime in **Comfort & updates**; it is cached on this PC and reused without further API calls.

Models default to `gemini-3.8-flash`, `eleven_v4_turbo` and `scribe_v2`; these are editable as provider access changes. For lower-cost speech, you can choose `eleven_flash_v2_5` if your account supports it. Voice ID is left for you to choose. Expressive v4/v3 models receive a gentle delivery cue for some moods; other models receive plain reply text. Voice is synthesized and disclosed in the interface. Windows demo voice quality and Hindi pronunciation depend on the voices already installed. Audio services are provided by ElevenLabs.

## Updates

Settings accepts a GitHub repository as `owner/name`; this build uses `psychspy7/lisa-companion`. **Check for updates** reads its latest public stable release. Each version must include **LISA.exe** and **SHA256SUMS.txt**. Lisa verifies the downloaded SHA-256, asks before installing, closes, replaces its executable using a hidden helper, and restarts. Personal data stays in a separate directory. A `.bak` copy of the previous executable is kept. A private repository requires signing in through the browser and manual downloading; this test updater currently uses unauthenticated public release downloads.

The executable is unsigned. Checksums detect corruption, but do not replace a code-signing certificate. Only configure a release repository you control or trust.

## Build from source

Use Python 3.12 on Windows with Tcl/Tk installed:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.\build.ps1
```

The build includes the artwork and audio dependency. `dist/LISA.exe` is the distributable. Run `python app.py` for development, `python -m unittest discover -s tests -v` for checks, or `python app.py --self-test` to render all poses and check startup/interruption without opening the microphone. Set `LISA_DATA_DIR` to a temporary folder for tests.

The included GitHub Actions workflow builds and publishes a stable release when you push a `v*` tag. Keep `core.VERSION` and `version.json` in agreement. Publishing requires an approved repository and Actions permissions.

## Local data

Settings, manually saved memory, optional chat history, cached chime and encrypted keys are in `%LOCALAPPDATA%\LISA`. Updating from 0.1 keeps saved notes and settings; Gemini and ElevenLabs keys must be added separately. A key encrypted for one Windows account cannot simply be copied to another. **Remove saved API keys** deletes locally saved credentials. Developers can alternatively use `GEMINI_API_KEY` and `ELEVENLABS_API_KEY` environment variables or a private `.env.local` beside the app/in up to three parent directories. Environment-provided keys are not removed by the Settings button. Deleting a memory note removes it from subsequent requests; it cannot recall content already sent to a provider. Environment files, keys, logs, local data, executables and build output are excluded by `.gitignore`.

## Next visual milestone

Replace sprite pose switches with a layered rig for smooth seated/standing transitions, accurate face deformation and phoneme-based lip sync. The current atlas files remain editable references for that upgrade.
