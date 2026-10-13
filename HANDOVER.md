# LISA 2.1 continuation guide

## Install and use

1. Run LISA-Setup.exe. Setup uses your Windows account and preserves existing Lisa data. Select the desktop-shortcut option if wanted.
2. Open Lisa. The Kitty Corp opening leads to Enter Lisa after the local room and artwork are ready.
3. Open the top-left menu → Chat & voice settings. Enter your chat/voice keys there and use Test connection. Keys are protected with Windows DPAPI. Never paste keys into chats or source files.
4. Alternatively, the approved owner can link Google and manage private credentials at https://lisa-control-center.kitty-ai.workers.dev. That console is owner-only, not a customer membership service. A fresh customer's app uses their own local keys.
5. Type naturally, or press Talk for continuous turn-taking. Speech is transcribed after a pause. Listening pauses during Lisa's speech; Interrupt lets you speak over it manually. Stop talk or quitting closes the microphone.
6. Room commands include go to the balcony, sit on the sofa, drink tea, go to sleep, wake up, lights on/off, go to the wardrobe, wash hands, exercise, stretch, read a book, use phone, wave, blow a kiss and wardrobe accessories. Private bathroom activities are not depicted explicitly.
7. Follow Lisa is saved. Right-drag temporarily adjusts the camera without clearing that choice. Use the menu checkbox to turn following off.

## Files you will need

- godot/project.godot, room-edit.tscn, main.gd, character.gd, camera_director.gd, room_routes.gd and bridge.gd: editable native engine project.
- godot/assets/: approved room GLB, layout, 32 pose frames arranged in eight atlases, provenance and intro artwork. The atlases are enhanced locally at 2x; they are not native 4K generations.
- desktop.py, godot_desktop.py, core.py, providers.py, routing.py, audio.py and gateway.py: retained native application services. Only chat, voice and transcription providers are active.
- persona.py and the Personality tab: default character guidance and private custom prompt. Saved notes remain separate from instructions.
- control-center/: Firebase/Cloudflare owner console and protected provider proxy. Keep OWNER_EMAIL and VAULT_KEY private; never rotate the vault key without re-encrypting existing rows.
- installer/, updates.py, updater_worker.py, installation.py and build.ps1: build, installer, update and restart behavior.
- tests/, licenses/, THIRD_PARTY_NOTICES.md and VERIFICATION.json: checks, attribution and actual release evidence.

## Continue yourself or with another AI

Extract the complete/source ZIP into a separate working folder. Clone this project's own GitHub repository if you need history, then overlay clean source while preserving .git. Read AGENTS.md, README.md and this guide first. The canonical local source remains under the Downloads Kitty-Corp workspace.

Install Python 3.12 dependencies from requirements.txt. Download Godot 4.7.2 Standard and matching Standard export templates. Use the editor to open godot/project.godot; .godot/ is a disposable import cache. Editing the room or character is separate from editing the native chat/voice service.

For a source run, set LISA_GODOT to the engine executable and LISA_DATA_DIR to an isolated test folder, then run app.py. For an automated check run app.py --self-test; it records scene checks and screenshots without opening a microphone or spending provider credits.

For a Windows build, use build.ps1 with -Python, -Godot, -Templates and optional -InnoCompiler arguments. Always build matching engine/templates. LISA.exe is the protected launcher/backend; engine/LISA-Engine.exe is its owned renderer. Keep them together.

The current appearance is illustrated 2.5D. Some actions are held pose cards, walking uses four illustrated frames, and facial animation is stylized. A complete deformable 3D likeness, continuous cloth/hair simulation, detailed hand contacts and all clothing combinations still need dedicated artist/rig work. Do not describe this build as a finished production 3D model.

## Publish an update

1. Make changes in the canonical Source repository, preserve personal data and the installer AppId.
2. Increase core.VERSION, version.json, Godot application/export versions and release notes together.
3. Run desktop/backend checks, Godot import/export, scene checks and the isolated clean-install plus real updater/restart test.
4. Build the fresh installer and compute its SHA-256. Include the bundled engine and its licenses in payload-manifest.json.
5. Commit verified source to this project's own repository, create a higher-version GitHub release and upload LISA-Setup.exe plus SHA256SUMS.txt. The installed updater prefers the installer.
6. Verify release asset sizes/digests and discovery. Never overwrite a published version's assets to simulate an update.
7. Refresh only Source File Zip/lisa using the provided archive updater after checks pass. Keep a verified complete ZIP for handover.

The updater's restart acknowledgment is emitted when Godot has loaded the room/title, before a human presses Enter. Closing the exact bundled engine releases its launcher and microphone. Private clips from older versions remain local but are no longer loaded.

## Commercial use

Godot is MIT and permits selling applications made with it. Keep GODOT-LICENSE.txt and GODOT-COPYRIGHT.txt with the application. The unmodified Python, Qt/PySide6 and other libraries keep their own notices and obligations. This build keeps Qt DLLs separate and supports rebuilding with compatible replacements.

The app does not contain company provider keys, a payment system or customer memberships. Customers can supply their own accounts. Check each provider's commercial API/voice terms and permission for any voice or artwork you distribute. ElevenLabs' free plan does not grant commercial audio use; eligible paid plans have separate terms: https://help.elevenlabs.io/hc/en-us/articles/13313564601361-Can-I-publish-the-content-I-generate-on-the-platform .

Windows signing is separate from the engine and installer. This test installer is unsigned; it is not a signed commercial release. Add your own publisher certificate when preparing a store/customer release, without changing Lisa's update/installation identity.

## Private data and recovery

%LOCALAPPDATA%/LISA holds local settings, protected keys, optional history, saved notes and update recovery files. Clean source ZIPs exclude those files, sessions, environment variables and live databases. Preserve them in your own private backup. Uninstalling/updating does not erase them.

The complete ZIP includes verified source, editable room/model references and original artwork inputs. The existing public GitHub repository preserves history; the ZIP intentionally omits .git and reproducible caches/dependencies.

## Release validation

89 desktop checks, 9 backend checks and 62 native pose/route/scene checks passed. A disposable installation verified the Desktop shortcut, file hashes, real GUI update callback, installer replacement, Godot restart acknowledgment and preservation of memory/custom prompt. Provider discovery was mocked for the update test; installation and restart were real. No account-funded API calls or actual microphone recording were made. The installer is unsigned. Performance was observed on Intel UHD Graphics under test/build load; no guaranteed frame rate on every PC. See packaged VERIFICATION.json.
