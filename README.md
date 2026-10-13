# LISA 2.1 · Godot Standard

A separate Windows companion app with an immersive 3D room, illustrated 2.5D Lisa, text chat, continuous turn-taking, cloud voice, saved memory and reviewed PC tools. Closing Lisa releases audio and exits its owned engine. Start-up keeps chat and the microphone off until you enter the room.

Install **LISA-Setup.exe** from this project's release. Godot 4.7.2 Standard is built in; no editor or .NET installation is required. The portable ZIP must be extracted completely; its LISA.exe needs the adjacent engine and _internal folders.

Use the compact top-left menu for chat/voice settings, memory, updates and the optional owner console. Customers can configure their own keys locally. The owner console remains restricted to the approved owner's Google identity; company keys and sessions are not shipped.

The character is illustrated 2.5D, not a deformable 3D production likeness. Read RELEASE_NOTES.md and VERIFICATION.json for supported behavior and testing limits.

## Development

Use Python 3.12, dependencies in requirements.txt, Godot 4.7.2 **Standard** and matching Standard export templates. No C#/.NET dependency is used.

Set LISA_GODOT to the official engine executable before running app.py. Run python -m unittest discover -s tests -v. Use a disposable LISA_DATA_DIR for self-tests; real provider calls and microphone tests need explicit user interaction.

Build with build.ps1 -Python <python.exe> -Godot <Godot executable> -Templates <extracted templates folder> -InnoCompiler <ISCC.exe>. The result is an app folder, portable ZIP and Inno installer. Preserve AppId, private data and update acknowledgment.

Editable engine project: godot/project.godot. Native protected services: desktop.py, godot_desktop.py, providers.py, audio.py, gateway.py. Private owner console: control-center/. Kept Three.js and Blender files are authoring/recovery references.

Read HANDOVER.md before continuing with another AI, selling a build or publishing updates. This project uses its own psychspy7/lisa-companion repository. Never merge it into another Kitty Corp repository. Private credentials and live data are excluded from clean archives.
