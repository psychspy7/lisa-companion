# LISA — your anime companion for Windows

LISA is a standalone Windows app created by Virat with the help of Kitty Corp organisation. Closing the app quits it and releases the microphone. Version **1.1.3** repairs update installation and automatic restart, while keeping your supplied Lisa icon, chat backups and hands-free conversation.

## Run

Download **LISA-Setup.exe**, close the old Lisa and run the installer. It installs for your Windows account, adds a Start Menu entry, and lets you choose a desktop shortcut. No administrator account is required. Open Lisa from that shortcut after installation. This also recovers an old test app whose Update button fails. Personal settings, encrypted keys, saved notes and optional history stay in `%LOCALAPPDATA%\LISA` across installation, updates and uninstall.

The installed app keeps its runtime files beside it, avoiding unpacking them on every launch. A portable `LISA.exe` is also published so older test versions can still discover and download this release. **Update** downloads a verified installer for installed editions, or a replacement executable for portable editions. A separate updater confirms it has started before Lisa closes, installs the new version, and restarts Lisa. It reports success after the new interface confirms its version. Installer logs are kept in the private `updates` folder; portable updates keep a backup. Progress and failures are shown in the app. If an older Update button fails after downloading, run the new Setup once to receive the repair. Uninstall removes application files and shortcuts while keeping personal Lisa data.

The app opens as its own fullscreen window on first launch and on the first upgrade to 1.0. **F11** toggles fullscreen; **Esc** stops speech and leaves fullscreen. Settings lets you choose windowed startup afterward. Drag the divider to resize chat, choose **Focus** to hide it, and use the zoom slider. Drag Lisa to reposition her; double-click to reset. **Ctrl+H** toggles chat. Choose **Start talk** for continuous conversation: speak, pause, hear Lisa, then speak again without pressing Send. Lisa pauses the mic during her reply to avoid echo; use **Interrupt** to cut her off and listen again. **End talk**, **Stop**, Esc, Settings or quitting ends the session. The mic stays off on every launch. **Mic** still records one message, up to 30 seconds. No camera. **Settings → App & privacy → Create desktop shortcut** can add a shortcut later.

## Configure services

You chose to enter keys in Settings later. No API keys are embedded in the app or public repository.

| Purpose | Service | Setup |
| --- | --- | --- |
| Chat and backups | Groq, Gemini, OpenRouter, Meta Llama | Separate API keys and available models; Meta needs a Llama developer key |
| Spoken replies | ElevenLabs | API key, Voice ID and speech model |
| Voice fallback / alternate | Fish Audio | API key, voice model ID; `s2.1-pro-free` is selectable |
| Microphone transcription | Groq, Gemini, ElevenLabs or Fish | Same provider key; configured backups work automatically |
| Action videos | Vidu | API key, then Generate in Motion Studio |
| Free voice preview | Installed Windows voice | No key; choose `windows` for primary voice |

Paste complete keys in **Settings → Chat**, then **Load models** and **Test connection** for each provider. Lisa's old Groq Llama defaults were retired for regular accounts; version 1.1 migrates those defaults to `openai/gpt-oss-120b`. Custom model choices are preserved. Choose another listed model if your account cannot access it. Gemini's JSON MIME type and model-specific configuration are repaired. Model listing confirms authentication, while Test connection checks an actual short reply and available quota.

With automatic backups enabled, Lisa tries the preferred service first, then configured Groq, Gemini, OpenRouter and Meta services once each. Missing keys are skipped. The status names the service that answered. Backup services receive the same chat context and saved notes. OpenRouter defaults to `openrouter/free`; select a paid model only if you want to spend that account's credits. Meta's key comes from the Llama developer platform; social-media tokens do not work. Load Meta models before testing because model access depends on your account.

For cloud speech, select a Voice ID as well as a key in **Settings → Voice**, then use that service's test button. ElevenLabs defaults to the economical Flash v2.5 model. If the chosen cloud voice fails, Lisa can try the other configured cloud voice and then an installed Windows voice. These choices are configurable. Windows voice quality and language support depend on installed voices. Continuous talk speaks replies even if the casual text-chat speech toggle is off.

Groq Whisper is the default transcription service; Gemini audio understanding, ElevenLabs or Fish can serve as configured backups. Speak for at least a quarter second and pause (default 0.85 seconds) to send. The detector retains a short pre-roll, ignores long silence, limits each spoken turn to 20 seconds, and stops the session with a visible error if every configured service fails. Adjust pause length and mic threshold for your room in Voice settings. This is automatic alternating speech, not simultaneous full-duplex audio or acoustic echo cancellation; interruption uses the Mic / Interrupt button.

Offline preview is labelled and uses preset responses. Start talk requires configured chat and transcription keys. Keys are protected with Windows DPAPI; screenshots of masked keys cannot configure Lisa. Missing, invalid, permission, retired-model, quota and network failures have distinct messages. Current local Lisa data has no configured keys for these providers, so authenticated live calls remain unverified; connection buttons let you validate your account directly. No credentials, chats or memories are bundled or published.

## Character and motion

Four matching full-body main portraits: morning casual, afternoon gym, evening black dress and night sleepwear. All 40 transparent assets are **2160 × 3840**, locally AI upscaled with Real-ESRGAN. This is upscaled 4K, not native 4K generation. The 36 expression artworks include sitting, commanding, angry, flying kiss, crying, tea and many others. Each expression has its own matching wardrobe; it is not available in every outfit.

Qt Quick uses graphic transforms for gentle breathing and sway, with fades between expressions. The old painted eye/mouth overlays are removed. These are illustrated poses and subtle motion, **not a fully rigged Live2D/3D model or phoneme lip sync**. Real action videos are supported through Vidu generation or MP4/WebM import. **No Vidu-generated clips are bundled yet because credentials were deferred.**

Motion Studio submits one explicit 4-second 1080p silent clip per Generate click, after showing the selection and asking before spending credits. It downloads completed jobs to a private local cache and resumes pending jobs when you reopen Lisa with a configured Vidu key. Generated clips use a fixed dark background. Jobs are not submitted automatically during chat. You can import clips without an API key. Provider contracts and fallback behavior are tested with mocked responses; authenticated calls still need testing with configured credentials.

## Personality, memory and PC actions

The Personality tab lets you write Lisa's style. The new default is candid, funny close-friend conversation: dry humor, Hinglish, playful roasts and invited bossiness, gentler listening when upset, and focused help for tasks. Existing custom prompts stay intact. The app supplies this creator answer: **I am made by Virat by the help of Kitty Corp organisation.** A style prompt does not bypass provider policies. Offline preview has preset lines and does not run your custom prompt.

Memory saves only notes you explicitly add. Chat history is off by default. Every PC action has a review dialog. Supported actions: open Calculator/Notepad/Explorer/browser, open a public HTTPS page, copy text, or save a `.txt` note to a location you choose. Arbitrary commands, deletions, purchases and messaging are unsupported. The model proposes actions; executable code is never taken from its reply.

## Build

Python 3.12 on Windows: `python -m pip install -r requirements.txt`, then `./build.ps1`. The GitHub Actions workflow builds tagged releases and publishes the installer, portable app and SHA-256 checksums. See `installer/` for the per-user Windows setup source. `python app.py --self-test` renders the app and checks shutdown; set `LISA_DATA_DIR` to an isolated test directory when using it. Automated tests use fake keys and mocked network responses.

Source and update releases: https://github.com/psychspy7/lisa-companion

Provider references: [Groq model retirement](https://console.groq.com/docs/deprecations), [Groq models](https://console.groq.com/docs/models), [Gemini structured output](https://ai.google.dev/gemini-api/docs/generate-content/structured-output), [OpenRouter API](https://openrouter.ai/docs/api/reference/overview), [Meta Llama API](https://github.com/meta-llama/llama-api-python), [Groq structured replies](https://console.groq.com/docs/structured-outputs), [Fish speech](https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech), [Fish emotions](https://docs.fish.audio/developer-guide/core-features/emotions), [Vidu image-to-video](https://platform.vidu.com/docs/image-to-video), [Vidu results](https://platform.vidu.com/docs/get-generation).

See ASSETS.md and THIRD_PARTY_NOTICES.md for artwork provenance and component licenses.
