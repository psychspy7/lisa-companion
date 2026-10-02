# LISA

Source and Windows releases: https://github.com/psychspy7/lisa-companion

A standalone Windows companion app starring Lisa: a clearly adult fictional anime character with midnight-blue hair, lavender tips, blue eyes, cat-ear accessories, and a warm, playful personality. She naturally calls you **Sir**.

## Try the test build

Open **LISA.exe** on Windows 10 or 11, 64-bit. No Python installation is needed. Close the window to quit completely. Lisa has no tray process, startup service, camera access, or background microphone listener.

The first launch uses **Free demo**, which has clearly labelled preset replies and your installed Windows voice. Try “chai”, “kiss”, “sit”, “motivate me”, “I am sad”, or “goodnight”. Turn on **Lisa’s voice** for spoken replies. Free demo is a visual and interaction preview, not a language model. It cannot transcribe voice input.

Uncheck **Free demo** to use OpenAI. Add your own OpenAI key in **Settings**, unless a local approved `.env.local` is available beside the app or in one of its three parent directories. API credits and internet are required. ChatGPT subscription billing is separate from API billing. If your API allowance is unavailable, use Free demo while configuring billing. Live AI chat, speech and transcription need verification with a funded API account.

**Talk** opens the microphone only when pressed in OpenAI mode. Press **Finish talking** to submit the recording, or **Stop/Escape** to discard it. Recording is limited to 30 seconds. Talk and Stop interrupt Lisa’s speech. Closing the app releases audio streams and exits the process. Voice recordings are held in memory and sent to OpenAI for transcription, then discarded. Text, saved notes, and voice text are sent to OpenAI when using AI mode. Camera stays off.

## Included in 0.1.0

- Four coordinated outfits for morning, afternoon, evening and night; selection by local PC time or manually.
- 36 illustrated poses: smile, shy, tea, sitting, wave, yawn, stretch, thinking, listening, commanding, angry, smirk, excited, laughing, surprised, proud, cheering, teasing, kiss, affectionate, elegant sitting, thumbs up, blushing, welcoming, apologetic, reassuring, peace, crying, sad, sleepy, goodnight, caring, pensive, self hug, cozy sitting and peaceful.
- Breathing/sway, software blinks on suitable unobscured faces, and audio-level mouth movement. Poses change as illustrations. This is a sprite prototype, not a fully rigged Live2D or 3D model. Some expressions already have closed eyes or covered mouths and suppress facial overlays.
- English, Hindi and Hinglish AI conversation with an editable choice of models and voice.
- Optional long-term notes in **Memory**, with add/remove controls. Chat history is off by default and optional in Settings.
- Local Windows DPAPI encryption for keys entered in Settings. No API key, personal memory or conversation is bundled.
- Soft UI chimes, configurable motion and sound, and an update button.

Models default to `gpt-4o-mini`, `gpt-4o-mini-tts` and `gpt-4o-mini-transcribe`; these are editable as provider models change. OpenAI voice is synthesized and disclosed in the interface. Windows demo voice quality and Hindi pronunciation depend on the voices already installed.

## Updates

Settings accepts a GitHub repository as `owner/name`. **Check for updates** reads its latest public stable release. Each version must include **LISA.exe** and **SHA256SUMS.txt**. Lisa verifies the downloaded SHA-256, asks before installing, closes, replaces its executable using a hidden helper, and restarts. Personal data stays in a separate directory. A `.bak` copy of the previous executable is kept. A private repository requires signing in through the browser and manual downloading; this test updater currently uses unauthenticated public release downloads. Until a release repository is approved/configured, the button explains setup.

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

Settings, manually saved memory, optional chat history and the encrypted key are in `%LOCALAPPDATA%\LISA`. A key encrypted for one Windows account cannot simply be copied to another. Deleting a memory note removes it from subsequent requests; it cannot recall content already sent to the API. Environment files, keys, logs, local data, executables and build output are excluded by `.gitignore`.

## Next visual milestone

Replace sprite pose switches with a layered rig for smooth seated/standing transitions, accurate face deformation and phoneme-based lip sync. The current atlas files remain editable references for that upgrade.
