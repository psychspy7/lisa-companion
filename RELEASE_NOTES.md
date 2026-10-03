LISA 1.1.3 repairs the update installation and automatic restart. After downloading and verifying a release, Lisa starts a separate updater and waits for its acknowledgement before closing. The updater installs into the existing folder, records an installer log, checks the installed version, and reopens Lisa. Success is reported only after the new Lisa confirms its version and interface loaded.

The handoff no longer depends on a hidden PowerShell script. Settings, encrypted API keys, memories and shortcut preferences stay in place. Portable updates retain a backup and restore it if the new app cannot launch.

If your existing version fails after downloading, close Lisa and run LISA-Setup.exe once to install this repair. Future updates use the repaired Update button. This release includes the supplied Lisa icon and all conversation features from 1.1.
