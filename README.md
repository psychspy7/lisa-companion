# LISA 2.0 — cinematic Windows companion

LISA is a separate Windows app made by Virat with the help of Kitty Corp organisation. It opens fullscreen into Lisa’s furnished room, with a small glass conversation bar and a settings menu at the top left. Closing it quits the app and releases microphone access.

This release is an **immersive development preview**. It combines the approved red-haired painted appearance in frontal idle shots with a real 52-bone 3D rig for walking, turning and actions. The model is an authored approximation of the reference, not a completed production anime model. Painted artwork cannot supply arbitrary unseen angles. Mouth movement follows speech volume, not phonemes. The 48 authored clips and 33 mesh objects are an editable foundation; hand contacts, cloth and likeness still need artistic refinement.

## Install and use

Run LISA-Setup.exe. The per-user installer checks folder access and installed payload hashes, preserves personal data and offers a desktop shortcut. Start Lisa from its shortcut. Settings → Check for updates uses the retained verified installer/portable updater and restarts the application; success is acknowledged after the assets and title load. Private data remains in %LOCALAPPDATA%/LISA.

Startup reports real loading progress, then plays a local candlelit throne reveal and waits for Enter Lisa. Click the button or press Enter to open the room. Skip bypasses the cinematic, while reduced motion uses a static title. The intro is silent. Chat and microphone remain inactive until entry. The updater acknowledges loaded assets and the title before human entry, so waiting at this screen does not fail the update.

Type “go to the balcony”, “have tea”, “go to sleep”, “wake up”, “lights off”, “exercise”, “remove sandals”, “wear sandals”, “wash hands”, “go to the toilet”, “take a shower”, “brush teeth”, “read a book”, “check phone”, “touch hair”, “take the whip”, or “put the whip back”. Lisa follows routed walking paths, completes posture transitions and performs supported actions. Bath/toilet scenes remain covered. The whip gesture is directed at empty space. Camera following can be disabled in the menu; dragging the room gives manual camera control. Quality controls limit the rendering resolution.

Tap the microphone to start continuous turn-taking: speech is sent after a pause, Lisa replies aloud, then listening resumes. Tap it again to end talk. The square button interrupts her reply and returns to listening if talk is active. This is continuous turn-taking, not simultaneous full-duplex voice recognition. Only Windows-native audio accesses the microphone. The room renderer has no microphone permission.

## Private control center

Open https://lisa-control-center.kitty-ai.workers.dev and sign in with the approved Google owner account. The backend verifies signed Firebase identity, Google provider, verified email, account state and a pinned administrator UID. Other accounts cannot control Lisa.

In the app’s menu choose Sign in with Google. Enter the six-digit code shown in Lisa into the private console’s device-link form. Linking is single-use and expires after five minutes. Google refresh credentials are encrypted with Windows DPAPI. On the first link, previously saved local provider keys that are absent from the vault are copied securely to the dedicated Lisa backend; existing cloud keys are preserved. Local recovery copies remain on this PC.

Manage Groq, Gemini, OpenRouter, Meta, ElevenLabs, Fish Audio and Vidu keys in the console. Provider keys are encrypted in Lisa’s Cloudflare D1 database using a Worker secret, are never returned to the browser or desktop, and stay out of Git and source archives. Load account-specific models/voices and test the selected providers. Configuration cannot make a retired model, exhausted quota or unavailable permission work. The code includes automatic chat, speech and transcription fallback.

Personal notes and optional chat history remain local. Settings → Saved memories saves only explicit notes. Requested chat sends bounded conversation context and saved notes to the configured provider. Camera access is not included. Supported PC actions retain a confirmation dialog; arbitrary shell commands, deletion, purchases and messaging are not available.

## Vidu and artwork

Motion Studio preserves explicit, credit-spending Vidu generation and private local clip imports. New native generations use the red-haired reference. A saved video can be reviewed in the muted local preview window. Vidu footage is a 2D clip and does not create or replace the room’s skeletal model. No generation starts automatically.

The native Three.js room is offline bundled under assets/suite. Its editable Blender model and source scripts are also supplied in the complete source archive. See ASSETS.md for original and generated asset provenance.

## Develop, update or hand over to another AI

Use Python 3.12 on Windows. Create a virtual environment, install requirements.txt, run python -m unittest discover -s tests -v, then python app.py. Use an isolated LISA_DATA_DIR for tests. Run build.ps1 to build installer, portable app and checksums. A compatible Inno Setup compiler is required; installer/install-compiler.ps1 prepares the pinned compiler.

The primary native entry is immersive_desktop.py. desktop.py retains chat, audio, memory, PC confirmations, motion jobs and updater behavior. gateway.py handles the protected cloud session. scene_actions.py limits the action vocabulary. assets/suite/runtime contains camera, room, action, prop and painted-appearance code. --legacy-ui opens the retained QML interface for recovery.

control-center contains the owner console and Worker. Use its project-local Node 24 or a compatible Node installation: npm ci, npm test, npm run build, then npm run deploy when you intend to publish. Deploy only the Lisa Worker and Lisa Firebase project. The OWNER_EMAIL and VAULT_KEY are deployment secrets; do not rotate the vault key without re-encrypting the existing provider vault. Firebase web configuration is public identity metadata, not a provider secret. Read control-center/README.md.

Create changes in Lisa’s existing Git repository, preserve its history, test the result, increment version.json and core.VERSION together, then publish the installer, portable executable and SHA256SUMS.txt with the matching tag. The app refuses version downgrades; 2.0.0 follows public 1.10.0. A release should not be marked ready solely because it compiled. Test a disposable installation and the restart acknowledgment.

Refresh Source File Zip/lisa/SOURCE-LATEST.zip with the workspace’s provided updater after verified changes. Never archive provider keys, Google refresh credentials, chats, personal notes, node_modules or build outputs. A handover archive contains source and editable assets, not a live credential or database backup. Restore deployment access separately through your own accounts.

Repository: https://github.com/psychspy7/lisa-companion
