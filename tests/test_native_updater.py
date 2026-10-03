import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch,MagicMock
import updates
import updater_worker as worker


class NativeUpdater(unittest.TestCase):
    def job(self,folder,kind='portable'):
        root=Path(folder);(root/'updates').mkdir()
        target=root/'LISA.exe';target.write_bytes(b'previous app')
        source=root/'updates/LISA-new.exe';source.write_bytes(b'new app')
        record={'id':'a'*32,'directory':str(root),'target':str(target),'source':str(source),
            'parent_pid':123,'kind':kind,'size':source.stat().st_size,'sha256':worker.file_hash(source),'version':'v1.1.3'}
        manifest=root/'updates/job.json';manifest.write_text(json.dumps(record))
        return root,target,source,manifest,record

    def test_parent_is_acknowledged_before_replacement_and_success_requires_new_version(self):
        with tempfile.TemporaryDirectory() as folder:
            root,target,source,manifest,record=self.job(folder)
            def parent_wait(seconds):
                self.assertTrue((root/'updates'/('ready-'+record['id']+'.json')).is_file())
                self.assertEqual(target.read_bytes(),b'previous app')
                return True
            parent=MagicMock();parent.wait.side_effect=parent_wait
            def launch(command,**kwargs):
                self.assertEqual(target.read_bytes(),b'new app')
                worker.write_json(kwargs['env']['LISA_UPDATE_ACK'],{'version':'1.1.3'})
                return MagicMock()
            with patch.object(worker,'Parent',return_value=parent),patch.object(worker,'close_other_windows'),patch.object(worker,'launch',side_effect=launch):
                self.assertEqual(worker.run_job(manifest),0)
            self.assertEqual(updates.read_update_status(root)['state'],'success')
            self.assertEqual(target.with_name('LISA.exe.bak').read_bytes(),b'previous app')
            parent.close.assert_called_once()

    def test_parent_that_cannot_close_keeps_original_and_does_not_duplicate_app(self):
        with tempfile.TemporaryDirectory() as folder:
            root,target,source,manifest,record=self.job(folder)
            parent=MagicMock();parent.wait.return_value=False
            with patch.object(worker,'Parent',return_value=parent),patch.object(worker,'launch') as launch:
                self.assertEqual(worker.run_job(manifest),1)
            launch.assert_not_called()
            self.assertEqual(target.read_bytes(),b'previous app')
            self.assertIn('closing',updates.pending_update_error(root))

    def test_failed_restart_restores_portable_version(self):
        with tempfile.TemporaryDirectory() as folder:
            root,target,source,manifest,record=self.job(folder)
            parent=MagicMock();parent.wait.return_value=True
            process=MagicMock();process.poll.return_value=1
            with patch.object(worker,'Parent',return_value=parent),patch.object(worker,'close_other_windows'),patch.object(worker,'launch',return_value=process) as launch:
                self.assertEqual(worker.run_job(manifest),1)
            self.assertEqual(target.read_bytes(),b'previous app')
            self.assertEqual(launch.call_count,2)
            self.assertEqual(updates.read_update_status(root)['state'],'error')

    def test_installer_must_report_expected_installed_version(self):
        with tempfile.TemporaryDirectory() as folder:
            root,target,source,manifest,record=self.job(folder,'installer')
            (root/'install-state.json').write_text(json.dumps({'application':'LISA','version':'1.0.0'}))
            (root/'_internal').mkdir();(root/'_internal/version.json').write_text('{"version":"1.0.0"}')
            parent=MagicMock();parent.wait.return_value=True
            process=MagicMock();process.wait.return_value=0
            with patch.object(worker,'Parent',return_value=parent),patch.object(worker,'close_other_windows'),patch.object(worker,'launch',return_value=process):
                self.assertEqual(worker.run_job(manifest),1)
            self.assertIn('expected Lisa version',updates.pending_update_error(root))

    def test_handoff_does_not_close_lisa_when_updater_cannot_start(self):
        with tempfile.TemporaryDirectory() as folder:
            root,target,source,manifest,record=self.job(folder)
            source.with_suffix('.json').write_text(json.dumps(record))
            bundled=root/'updater.exe';bundled.write_bytes(b'updater fixture')
            process=MagicMock();process.poll.return_value=1
            with patch('updates.sys.frozen',True,create=True),patch('updates.sys.executable',str(target)),patch('core.resource',return_value=bundled),patch('updates.subprocess.Popen',return_value=process):
                with self.assertRaisesRegex(updates.UpdateError,'could not start'):
                    updates.install_update(source,root)


if __name__=='__main__':unittest.main()
