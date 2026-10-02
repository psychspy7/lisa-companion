# LISA — your anime companion for Windows

LISA is a standalone Windows app created by Virat with the help of Kitty Corp organisation. Closing the app quits it and releases the microphone. Version 0.3.0 is a test release.

## Run

Download `LISA.exe` and run it from a writable folder. Use the **Update** button for future GitHub releases. Personal settings, keys, saved notes and optional history stay in `%LOCALAPPDATA%\LISA` across updates.

The app opens fullscreen. **F11** toggles fullscreen; **Esc** stops speech and leaves fullscreen. Drag the divider to resize chat, choose **Focus** to hide it, and use the zoom slider. Drag Lisa to reposition her; double-click to reset. **Ctrl+H** toggles chat. Press Mic to start recording and again to submit; recordings stop after 30 seconds. Stop interrupts speech and discards late replies. No background listening or camera.

## Configure services

You chose to enter keys in Settings later. No API keys are embedded in the app or public repository.

| Purpose | Service | Setup |
| --- | --- | --- |
| Chat | Groq, or Gemini | API key and a model available to your account |
| Spoken replies | ElevenLabs | API key, Voice ID and speech model |
| Voice fallback / alternate | Fish Audio | API key, voice model ID; `s2.1-pro-free` is selectable |
| Microphone transcription | Groq, ElevenLabs or Fish | Same provider key; Groq defaults to Whisper Large V3 Turbo |
| Action videos | Vidu | API key, then Generate in Motion Studio |
| Free voice preview | Installed Windows voice | No key; choose `windows` for primary voice |

Save a Groq key, then use **Load my available Groq models**. Llama 3.3 70B is the preferred character model when your account can access it. Groq's current public documentation lists Llama models as Enterprise, so free accounts may need another available model. Lisa never silently switches a paid chat model. Gemini Flash-Lite remains selectable; the supplied account table gives it a larger daily allowance than regular Flash. Provider quotas, permissions and prices can change.

Enable **Speak Lisa's replies** after choosing a voice. ElevenLabs failure tries Fish once only when fallback is enabled and its key and voice ID are set. The status names the fallback. Offline preview is labelled and uses preset responses, not a language model. Keys are protected with Windows DPAPI for the current Windows user.

## Character and motion

Four matching full-body main portraits: morning casual, afternoon gym, evening black dress and night sleepwear. All 40 transparent assets are **2160 × 3840**, locally AI upscaled with Real-ESRGAN. This is upscaled 4K, not native 4K generation. The 36 expression artworks include sitting, commanding, angry, flying kiss, crying, tea and many others. Each expression has its own matching wardrobe; it is not available in every outfit.

Qt Quick uses graphic transforms for gentle breathing and sway, with fades between expressions. The old painted eye/mouth overlays are removed. These are illustrated poses and subtle motion, **not a fully rigged Live2D/3D model or phoneme lip sync**. Real action videos are supported through Vidu generation or MP4/WebM import. **No Vidu-generated clips are bundled yet because credentials were deferred.**

Motion Studio submits one explicit 4-second 1080p silent clip per Generate click, after showing the selection and asking before spending credits. It downloads completed jobs to a private local cache and resumes pending jobs when you reopen Lisa with a configured Vidu key. Generated clips use a fixed dark background. Jobs are not submitted automatically during chat. You can import clips without an API key. API connection contracts are tested with mocked responses; live Groq, Fish and Vidu calls still need testing with your credentials.

## Personality, memory and PC actions

The Personality tab lets you write Lisa's style: warm close-friend conversation, Hinglish, playful roasts and mock bossiness, gentler listening when upset, and focused help for tasks. The app supplies this creator answer: **I am made by Virat by the help of Kitty Corp organisation.** A style prompt does not bypass provider policies.

Memory saves only notes you explicitly add. Chat history is off by default. Every PC action has a review dialog. Supported actions: open Calculator/Notepad/Explorer/browser, open a public HTTPS page, copy text, or save a `.txt` note to a location you choose. Arbitrary commands, deletions, purchases and messaging are unsupported. The model proposes actions; executable code is never taken from its reply.

## Build

Python 3.12 on Windows: `python -m pip install -r requirements.txt`, then `./build.ps1`. The GitHub Actions workflow builds tagged releases and publishes `LISA.exe` plus a SHA-256 checksum. `python app.py --self-test` renders the app and checks shutdown; set `LISA_DATA_DIR` to an isolated test directory when using it. Automated tests use fake keys and mocked network responses.

Source and update releases: https://github.com/psychspy7/lisa-companion

Provider references: [Groq models](https://console.groq.com/docs/models), [Groq structured replies](https://console.groq.com/docs/structured-outputs), [Fish speech](https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech), [Fish emotions](https://docs.fish.audio/developer-guide/core-features/emotions), [Vidu image-to-video](https://platform.vidu.com/docs/image-to-video), [Vidu results](https://platform.vidu.com/docs/get-generation).

See ASSETS.md and THIRD_PARTY_NOTICES.md for artwork provenance and component licenses.