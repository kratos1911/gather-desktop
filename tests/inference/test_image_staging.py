"""Small fake wheelhouses; no package installation or model access."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scripts import prepare_inference_image as staging


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=staging.ROOT / 'output')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.build = self.root / 'output/candidate'
        (self.build / 'wheels').mkdir(parents=True)
        source = self.root / 'services/inference'
        source.mkdir(parents=True)
        worker = self.root / 'services/worker'
        worker.mkdir()
        for name in ('runtime.py','qwen.py','stream.py','chunking.py','asgi.py',
                     'service_auth.py','managed_auth.py','startup.py','artifacts.py','model-manifest.json','Dockerfile'):
            (source / name).write_text('# fixture')
        for name in ('service_transport.py','embedding_client.py','service_clients.py','cloud_identity.py'):
            (worker / name).write_text('# fixture')
        wheel = self.build / 'wheels/fixture-1-py3-none-any.whl'
        with zipfile.ZipFile(wheel,'w') as archive:
            archive.writestr('fixture-1.dist-info/METADATA','Name: fixture\nVersion: 1\n')
        (source / 'requirements.lock').write_text('fixture==1 --hash=sha256:'+staging.digest(wheel)+'\n')
        self.patch = patch.object(staging,'ROOT',self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.zlib_patch = patch.object(staging, 'stage_zlib')
        self.zlib_patch.start()
        self.addCleanup(self.zlib_patch.stop)

    def test_serving_stages_without_model_and_excludes_stale_code(self):
        stale = self.build / 'services/inference/unreviewed.py'
        stale.parent.mkdir(parents=True)
        stale.write_text('secret fixture')
        staging.prepare(self.build, update_lock=True, serving=True)
        self.assertTrue((self.build / 'services/inference/asgi.py').exists())
        for name in ('service_auth.py','managed_auth.py','startup.py','artifacts.py','model-manifest.json'):
            self.assertTrue((self.build / 'services/inference' / name).exists())
        policy = (self.build / '.dockerignore').read_text()
        self.assertNotIn('!services/inference/*.py',policy)
        self.assertNotIn('unreviewed',policy)
        self.assertIn('!third-party-notices.json',policy)
        self.assertTrue((self.build / 'third-party-notices.json').exists())
        self.assertFalse((self.root / 'output/inference-model').exists())
        staging.prepare(self.build, serving=True)

    def test_modified_model_wheel_rejected_before_lock_write(self):
        wheel = next((self.build / 'wheels').glob('*.whl'))
        with zipfile.ZipFile(wheel,'a') as archive:
            archive.writestr('extra.txt','changed')
        with self.assertRaisesRegex(ValueError,'pinned model'):
            staging.prepare(self.build, update_lock=True, serving=True)
        self.assertFalse((self.root / 'services/inference/requirements-serving.lock').exists())

    def test_changed_serving_lock_requires_explicit_update(self):
        (self.root / 'services/inference/requirements-serving.lock').write_text('old review')
        with self.assertRaisesRegex(ValueError,'reviewed lock'):
            staging.prepare(self.build, serving=True)

    def test_outside_output_rejected(self):
        with self.assertRaisesRegex(ValueError,'output directory'):
            staging.prepare(self.root / 'outside', serving=True)

    def test_missing_required_attribution_blocks_staging(self):
        with patch.object(staging, 'collect', return_value={'supplements': []}):
            with self.assertRaisesRegex(ValueError, 'required upstream attribution'):
                staging.prepare(self.build, update_lock=True, serving=True)
        self.assertFalse((self.build / 'third-party-notices.json').exists())


if __name__ == '__main__':
    unittest.main()
