# Using and changing Lisa

Install LISA-Setup.exe. Choose the optional Desktop shortcut. Open Lisa, enter your personal access code online once, then enter the room after the opening. The main app opens fullscreen; Escape opens the small menu and Fullscreen can return it to a normal window.

Use the small footer to type, or Talk for continuous turn-taking. Add your own chat/transcription/voice API keys in Settings and use Test connection. Never paste keys into a public chat or source file. With no working chat provider, Lisa uses the local offline companion. Speech recognition still needs internet and a configured transcription service; local routines and text chat do not. Interrupt ends the current response/action. Closing Lisa quits the engine/backend and stops microphone access.

Examples: Go to the balcony; sit on the sofa; have tea; do exercise; take a shower; go to the bathroom; go to sleep; wake up; lights off; lights on; change outfit; give me a kiss. Rooms use walking paths. Bathroom and shower are private transitions; Lisa automatically walks back. Showers alternate the two outfit looks. Daily routines, optional affection and room effects are in the small menu. Save personal details deliberately in Memory.

For personality, open Settings and edit Character guidance. Source persona.py contains the default full prompt. The continuation prompt included in the handover is for a developer AI, not Lisa's personality. Keep your custom prompt backed up in private settings. Lisa is a fictional AI companion; the app does not provide genuine human consciousness.

For a future change yourself: extract the complete ZIP, read HANDOVER.md and CONTINUATION-PROMPT.md, clone the existing repository if you need Git history, copy clean Source files over it and restore Offline-Assets into Source/offline. Open Godot/project.godot in the matching Standard editor to edit the room/character. Python files control providers, keys, voice and licensing; Godot files control graphics and movement. Change only the part you need and test it before building.

To work with another AI: provide the clean source/Godot project plus CONTINUATION-PROMPT.md and explain your new request. Do not share the owner sale codes or signing backup. The public repository can be supplied instead of a huge ZIP when only code is needed.

For an update: raise version.json, core.VERSION, Godot project/export version and backend package metadata together. Build and verify installer, portable and restart using the existing updater. Keep the same Inno AppId and private data folder. Publish the new release and its SHA256SUMS.txt to the same repository after checks. Lisa's Update button selects its edition, verifies the download, runs the installer/helper, then restarts the new app and waits for its native-room acknowledgment. Do not upload an unfinished test as Latest.

Activation sales: keep the separate private code CSV, send one unclaimed code per buyer, and keep a private license ledger. Read tools/ACTIVATION.md for recovery/limits. The Buy Lisa button opens the existing Kitty Corp site; automated checkout/code delivery is not added by this release.
