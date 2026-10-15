# LISA 2.2.0 handover

Read OWNER-GUIDE.md for use and updates, CONTINUATION-PROMPT.md for another AI, tools/ACTIVATION.md for private code administration, and VERIFICATION-SUMMARY.md for actual test limits.

## Architecture and important files
- app.py -> desktop.py -> godot_desktop.py launches the native Godot Standard engine. Python owns keys, voice, history/memory, confirmations and updates.
- godot/project.godot is the editable engine project; main.gd handles UI, intro, routes and activities; character.gd and artwork_common.gdshaderinc control illustrated motion; camera_director.gd follows Lisa; room_routes.gd contains walkable paths.
- godot/assets contains the room, directional/pose atlases and poses.json. godot/media contains the supplied opening and original synthesized quiet effects.
- persona.py is the full default character prompt; core.py holds factual/tool guardrails and private settings. Settings -> Character guidance overrides style. Saved Memory notes are selected data, never automatic training.
- providers.py/routing.py/audio.py handle online chat, continuous turn-taking, voice and fallback. offline_companion.py supplies immediate grounded intents plus bounded local CPU inference. offline/manifest.json pins model/runtime provenance; tools/verify_offline.py verifies restored assets.
- activation.py/activation_ui.py enforce the first-launch gate; activation-public.json pins public receipt verification. control-center/src/licensing.js and migrations/0002_activation.sql implement atomic redemption, proof/recovery and rate limits. tools/manage_activation.py is owner-only provisioning.
- installer/LISA.iss, build_setup.py, build_godot.py, installation.py, updates.py and updater_worker.py preserve installer identity, payload/download integrity and verified restart.
- control-center contains the existing separate Cloudflare/Firebase-protected owner site. Its Google login remains private administration; customers activate with a code and use BYOK/offline.

## Build from the full handover
Use Windows x64, Python3.12, Godot4.7.2 Standard official ed1daf0bf with matching Standard Windows export templates, and InnoSetup6.7+. No .NET runtime/editor is needed to run the installed app.

Extract Source/SOURCE-LATEST.zip; the editable Godot project is Source/godot. Extract Assets/LISA-Offline-Assets.zip into that Source folder so offline/model.gguf and offline/runtime exist. Run python tools/verify_offline.py. The clean source GitHub/archive intentionally omit the ~675MB model and runtime executables; their exact bytes are included separately in the full handover, not downloaded every launch.

Create a Python3.12 venv; install requirements.txt. For owner console, install its package-lock.json with npm ci. Source run needs LISA_GODOT set to the verified editor EXE. Source run still needs valid device activation; no bypass is supplied. Use isolated LISA_DATA_DIR for QA and preserve an activated test identity.

Build:
```powershell
./build.ps1 -Python ./venv/Scripts/python.exe -Godot C:/Tools/Godot/Godot_v4.7.2-stable_win64.exe -Templates C:/Tools/Godot/4.7.2.stable -InnoCompiler "C:/Program Files (x86)/Inno Setup 6/ISCC.exe"
```
The matching templates directory needs windows_release_x86_64.exe and version.txt. Run backend tests in control-center. Test the installed EXE, native room, scene timers, cancellation, clean install and actual updater/helper/restart in a disposable folder before a public release. Never validate by replacing the owner's real install/data.

## Updating and preservation
Use a higher semantic version next (e.g.2.2.1), update version.json/core.VERSION/Godot export/project/backend metadata consistently, retain Inno AppId A8F7C393-8F62-4CD1-ACE5-65F949F74543, build separate installer/portable, publish SHA256SUMS.txt to psychspy7/lisa-companion. Update must download/verify before close, run installer, restart backend+engine, and wait for native ready acknowledgment. Activation keys/receipt, provider credentials, saved notes/history/custom style stay in LocalAppData/LISA.

Owner secrets/live D1/Firebase data, the 50 sale codes, protected provider keys and user data are outside public source/packages. Keep private backups separately. Never rotate VAULT_KEY or the activation signing key during routine upgrades. A lost device identity requires owner replacement; a copied lifetime receipt cannot be used on another machine by the normal client. Offline DRM is not tamper-proof and does not revoke an already issued lifetime receipt.

## Exact product limits
Lisa is an illustrated2.5D actor in a real3D room, with small anchored deformation/crossfades, four walk frames and stylized frontal face motion. It is not a production 3D/Live2D likeness; no real bone/contact simulation is claimed. Midnight/Burgundy are two coordinated tint variants of the same outfit silhouette.

Offline text generation is a small CPU fallback, not cloud-quality intelligence or real human consciousness. Routines require the app to stay open; no background companion/microphone after quitting. Offline speech input is not included; transcription needs a configured service. Bathroom is a discreet10s privacy transition plus ordinary flush; shower15s privacy/water then alternate outfit and return walk. Affectionate autonomous gestures default off and respect conversation priority. No whip scene.

The installer is unsigned. No real microphone capture or account-funded provider call is part of automated QA. Notices include Godot/llama.cpp MIT and Qwen Apache2.0; supplied artwork/video and chosen voice/provider distribution rights remain owner responsibilities.
