# Windows installer

LISA-Setup.exe uses Inno Setup 6.7.3. It installs the pre-extracted application in
`%LOCALAPPDATA%\Programs\LISA`, adds a Start Menu shortcut, offers an optional
Desktop shortcut, and registers a standard uninstaller for the current user.
No administrator privileges are required. The installer and uninstaller never
remove `%LOCALAPPDATA%\LISA`, which holds private credentials, chats and memory.

`build.ps1` builds both the portable `LISA.exe` for older updater compatibility
and the fast-starting `LISA-App\LISA.exe` installed layout before compiling setup.
Use `-InnoCompiler <path to ISCC.exe>` or set `LISA_ISCC` locally. The release
workflow downloads the pinned official compiler and validates its SHA-256 and
Authenticode signature before using its portable mode. Compiler files are not
published with Lisa.

Installed updates pass `/SILENT /SUPPRESSMSGBOXES /NORESTART /SP- /UPDATE
/DIR="<current install>"` after Lisa closes. Setup preserves the recorded shortcut
choice; `/UPDATE` suppresses setup's launch option so only the updater restarts
the app after a successful install. Existing portable versions can still update
through the `LISA.exe` release asset, then offer the standard installer.

For isolated lifecycle QA, `installer/build_setup.py <output> --test-build`
compiles the same payload with uninstall registration disabled and shortcuts
redirected to `Desktop` and `Start Menu` beside the chosen application folder.
Pass `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /DIR="<QA folder>\LISA"
/TASKS="desktopicon"` to test installation without modifying real user shortcuts.

Inno Setup is by Jordan Russell and Martijn Laan, used without modification.
Official documentation and license: https://jrsoftware.org/ and
https://github.com/jrsoftware/issrc/blob/main/LICENSE.TXT.
