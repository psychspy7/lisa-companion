"""Compile the standard per-user Windows installer from the onedir app."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def find_compiler(explicit=None):
    options = [explicit, os.environ.get("LISA_ISCC"), shutil.which("ISCC.exe")]
    for variable in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        root = os.environ.get(variable)
        if root:
            options.extend([str(Path(root) / "Inno Setup 6" / "ISCC.exe"),
                            str(Path(root) / "Programs" / "Inno Setup 6" / "ISCC.exe")])
    for option in options:
        if option and Path(option).is_file():
            return Path(option).resolve()
    raise RuntimeError("Inno Setup 6.7+ compiler was not found. Install it or set LISA_ISCC to ISCC.exe.")


def prepare_payload(app, version, output):
    app,output=Path(app).resolve(),Path(output).resolve()
    required=['LISA.exe','_internal/version.json','_internal/ui/Main.qml',
        '_internal/updater/LISA-Updater.exe','_internal/assets/lisa.ico']
    if any(not (app/name).is_file() for name in required):
        raise RuntimeError('Installed payload is incomplete: app, UI, version, icon and native updater are required.')
    if json.loads((app/'_internal/version.json').read_text())['version']!=version:
        raise RuntimeError('The built application version differs from version.json. Rebuild the app first.')
    artwork=list((app/'_internal/assets').rglob('*.webp'))
    if len(artwork)!=40:raise RuntimeError('The complete 40-file character artwork is required.')
    (app/'install-state.json').write_text(json.dumps({
        'application':'LISA','format':1,'version':version,'installer':'inno','verified_payload':1,
    },indent=2)+'\n',encoding='utf-8')
    files=[]
    for path in sorted(app.rglob('*')):
        if path.is_file() and path.name!='payload-manifest.json':
            with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
            files.append({'path':path.relative_to(app).as_posix(),'sha256':digest})
    manifest=app/'payload-manifest.json'
    manifest.write_text(json.dumps({'application':'LISA','version':version,'files':files},indent=2)+'\n',encoding='utf-8')
    checks=files+[{'path':'payload-manifest.json','sha256':hashlib.sha256(manifest.read_bytes()).hexdigest()}]
    lines=['procedure VerifyInstalledPayload;', 'begin']
    for item in checks:
        relative=item['path'].replace('/', '\\').replace("'", "''")
        lines.append("  VerifyInstalledFile('"+relative+"', '"+item['sha256']+"');")
    lines.append('end;')
    include=output/'payload-checks.iss';include.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return include


def build(output, compiler=None, test_build=False):
    source = Path(__file__).resolve().parent
    output = Path(output).resolve()
    app = output / "LISA-App"
    if not (app / "LISA.exe").is_file() or not (app / "_internal").is_dir():
        raise RuntimeError("Build lisa-installed.spec first; LISA-App/LISA.exe and _internal are required.")
    version = json.loads((source.parent / "version.json").read_text(encoding="utf-8"))["version"]
    include=prepare_payload(app,version,output)
    args = [str(find_compiler(compiler)), "/Qp", "/DAppVersion=" + version,
            "/DAppSource=" + str(app), "/DOutputPath=" + str(output), '/DVerificationInclude='+str(include)]
    if test_build:
        args.append("/DTestBuild")
    subprocess.run(args + [str(source / "LISA.iss")], check=True)
    lines = []
    for name in ("LISA.exe", "LISA-Setup.exe"):
        path = output / name
        if path.is_file():
            with path.open("rb") as stream:
                lines.append(hashlib.file_digest(stream, "sha256").hexdigest() + "  " + name)
    (output / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Built " + str(output / "LISA-Setup.exe"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("--compiler")
    parser.add_argument("--test-build", action="store_true", help="Isolate shortcuts and skip uninstall registration for QA.")
    args = parser.parse_args()
    build(args.output, args.compiler, args.test_build)
