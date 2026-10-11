# Lisa 1.10: use, change and publish

This release restores the companion after the 1.9.3 maintenance screen. It is an immersive development preview. The painted frontal idle appearance matches the red-haired reference; free movement uses the editable 3D approximation. Refining that model's likeness, cloth and contact poses remains separate artistic work. Do not describe the painted layer as a complete deformable avatar.

## Install this version

1. Close Lisa and run LISA-Setup.exe. Keep the existing default destination. Setup offers a desktop shortcut and verifies the installed files.
2. Open Lisa. The black Kitty Corp reveal waits for the room assets to load. The app opens fullscreen; the menu provides fullscreen/window and quality controls.
3. Open the top-left menu and choose Sign in with Google. A private browser page opens. Sign in with the existing approved owner account and submit the six-digit code shown in the desktop app.
4. Missing cloud provider keys migrate from this PC's saved encrypted keys after linking. Existing vault keys are preserved. Otherwise add and test keys in the private control center: https://lisa-control-center.kitty-ai.workers.dev.
5. Choose chat, speech and transcription models available to your accounts. Quotas, model availability and provider permissions still apply. No real paid provider generation was used to validate this release.
6. Type a direct room command, such as "go to the balcony" or "have tea". Tap the microphone to start continuous turns and tap again to stop. The square interrupt button stops Lisa's speech.

Private memories, prompts, optional history and recovery keys remain under %LOCALAPPDATA%/LISA. Installer repair and updates preserve this folder. Closing Lisa stops its audio and microphone. The web room has no microphone permission.

## How to change Lisa yourself

The clean source archive contains Source, 3D-Interaction-Review, Room-Review, a manifest and continuation tools. Extract it in a separate folder and read CONTINUE.md. For history, clone https://github.com/psychspy7/lisa-companion, then overlay Source onto that checkout without replacing its .git directory.

Use Python 3.12 on Windows. Install Source/requirements.txt into a virtual environment. Set LISA_DATA_DIR to a disposable folder before testing; run the desktop tests with python -m unittest discover -s tests -v. Start with python app.py. Build with Source/build.ps1 and a compatible Inno Setup compiler. Do not point test installs or test data at the user's real application.

Important files:

| Purpose | Location under Source |
| --- | --- |
| Native fullscreen window, web bridge, opening acknowledgment | immersive_desktop.py |
| Conversation, continuous voice, memory, PC confirmations, updater | desktop.py |
| Firebase desktop linking and private backend calls | gateway.py |
| Lisa personality, settings and version | core.py, version.json |
| Closed room commands | scene_actions.py |
| Camera and room | assets/suite/runtime/suite.js, cinematic-camera.js |
| Walking, transitions and action cycles | assets/suite/runtime/room-avatar.js |
| Props, sandals and sleeves | assets/suite/runtime/scene-props.js |
| Painted idle appearance | assets/suite/runtime/painted-appearance.js |
| Black opening and reveal | assets/suite/runtime/opening.js |
| Transparent conversation interface | assets/suite/runtime/room.html, native-bridge.js |
| Local Vidu clip review | motion_preview.py |
| Installer and payload verification | installer/LISA.iss, installer/build_setup.py |
| Update download and safe install/restart | updates.py, updater_worker.py |
| Owner console and Cloudflare API | control-center/src, control-center/public |
| Desktop regression tests | tests |

The editable Blender file and authoring scripts are in 3D-Interaction-Review/source. The current model has 52 bones and 48 clips. Keep the runtime bone/clip names compatible when exporting replacements. Test walking routes, sitting/standing, lying/getting up, sandals, sleeves, props, camera following, speech and interruption. Do not silently replace the current asset with a different character.

## Give another AI the project

Give it the clean ZIP and this instruction:

"Continue this existing Lisa repository. Read README.md, HANDOVER.md, AGENTS.md and CONTROL-CENTER-SETUP.md before changes. Preserve its Git history and updater identity. Use an isolated data folder for tests. Provider keys, Google sessions, chats and deployment secrets are excluded; do not ask me to paste them into chat. First inspect the current implementation and verified reports. Keep fullscreen native chat, continuous turn-taking, explicit PC confirmations and the private console. The present avatar is a hybrid preview; improve the real 3D model without claiming the painted idle layer works at every angle. Make the requested changes, test a disposable install and real updater restart, refresh the source snapshot, then publish only to psychspy7/lisa-companion when I authorize a release."

Supply the specific feature you want changed after that instruction. Another AI needs access to the existing repository and your deployment accounts only if the change affects them.

## Publish the next update

1. Create a branch from current main. Make and test the change.
2. Increase core.VERSION and version.json together. 1.10.1 is a suitable next patch; do not publish 1.9.0 because users already have a newer version.
3. Build the portable app, installer and SHA256SUMS.txt. Keep the installer AppId and private data location unchanged.
4. Verify a disposable clean install, shortcut, update from an older version, restarted room acknowledgment and preservation of personal settings. A successful compilation alone is insufficient.
5. Push the source and create the matching GitHub release with the installer, portable executable and SHA256SUMS.txt. Mark it ready only when those exact files have passed verification.
6. The app's Check for updates reads the latest public release. It downloads and validates the payload, closes Lisa, installs, restarts it and acknowledges success after the room loads.
7. Refresh Source File Zip/lisa/SOURCE-LATEST.zip using the workspace's provided updater after verified changes.

## Backend changes and recovery

The deployed Worker is lisa-control-center on the kitty-ai.workers.dev account, using its own lisa-control-center D1 database. Firebase project: lisa-kittycorp-20261011. Use only these Lisa resources, separately from Kitty AI.

In control-center use Node 24.12 or newer, npm ci, npm test and npm run build. npm run deploy publishes the Worker and requires your Cloudflare login. Firebase auth changes require Firebase CLI access to the dedicated project. Existing account sign-in has been verified.

OWNER_EMAIL and VAULT_KEY are Worker secrets. Never print them or commit them. Do not rotate VAULT_KEY unless the existing vault is re-encrypted first. Source backups cannot restore encrypted provider keys without the correct deployed secret. Back up or migrate live D1 and deployment access privately through your own account tools.

The ZIP excludes secrets, chats, personal memories, refresh tokens, dependency folders, build caches and the .git directory. Git history remains in the existing local and GitHub repository. A source ZIP is not a live database backup.

## What was verified and what remains

Desktop/provider logic, cloud identity/vault validation, room routes/actions, native UI startup, clean installation and real installer/update/restart are covered by the supplied verification report. Room checks use a software renderer and accelerated simulation; they are functional checks, not a claim about frame rate on your PC.

Real keys, paid TTS/STT, Vidu generation and physical microphone quality must be tested with your own accounts after desktop linking. Voice is continuous turn-taking with manual interruption, not simultaneous full-duplex recognition. Facial motion follows audio volume; it is not phoneme-based lip sync. The model's production likeness, garment simulation and precise hand contacts remain unfinished.
