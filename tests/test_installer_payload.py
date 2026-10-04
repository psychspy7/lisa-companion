import json
from pathlib import Path
import tempfile
import unittest
from installer.build_setup import prepare_payload


class InstallerPayload(unittest.TestCase):
    def payload(self,root):
        app=root/'LISA-App'
        for name in ('LISA.exe','_internal/ui/Main.qml','_internal/updater/LISA-Updater.exe','_internal/assets/lisa.ico'):
            path=app/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'fixture')
        (app/'_internal/version.json').write_text('{"version":"1.9.1"}')
        for i in range(40):(app/'_internal/assets'/f'{i}.webp').write_bytes(b'fixture')
        return app

    def test_incomplete_or_wrong_version_payload_cannot_be_packaged(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);app=self.payload(root)
            with self.assertRaisesRegex(RuntimeError,'version differs'):prepare_payload(app,'9.9.9',root)
            (app/'_internal/updater/LISA-Updater.exe').unlink()
            with self.assertRaisesRegex(RuntimeError,'incomplete'):prepare_payload(app,'1.9.1',root)

    def test_manifest_checks_all_payload_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);app=self.payload(root)
            include=prepare_payload(app,'1.9.1',root)
            manifest=json.loads((app/'payload-manifest.json').read_text())
            self.assertEqual(len(manifest['files']),46)
            self.assertIn('payload-manifest.json',include.read_text())
            self.assertEqual(json.loads((app/'install-state.json').read_text())['verified_payload'],1)
            self.assertEqual(len(prepare_payload(app,'1.9.1',root).read_text().splitlines()),50)


if __name__=='__main__':unittest.main()
