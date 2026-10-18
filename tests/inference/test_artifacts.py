"""Small synthetic files test integrity gates; no model load or network."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from services.inference import artifacts
from services.inference.startup import build_verified_app
from services.inference.runtime import MODEL, REVISION


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        # D: on the host, bounded tmpfs inside Linux checks.
        root = Path(__file__).resolve().parents[2] / 'output'
        self.temp = tempfile.TemporaryDirectory(dir=root if root.is_dir() else None)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.model = self.root / 'model'
        self.model.mkdir()
        self.content = b'fictional weights'
        (self.model / 'model.safetensors').write_bytes(self.content)
        self.manifest = dict(model=MODEL, revision=REVISION, expected_bytes=len(self.content),
            artifacts=[dict(file='model.safetensors', bytes=len(self.content),
                            sha256=hashlib.sha256(self.content).hexdigest())])
        self.path = self.root / 'manifest.json'
        self.save()
        self.patch = patch.object(artifacts, 'MANIFEST', self.path)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def save(self):
        self.path.write_text(json.dumps(self.manifest), encoding='utf-8')

    def test_valid_snapshot_and_deferred_runtime(self):
        self.assertEqual(artifacts.verify_snapshot(self.model), self.model)
        policy = json.dumps({'audience':'https://gather-test.run.app','callers':[
            {'email':'gather-api@sample-project.iam.gserviceaccount.com','subject':'123'}]}).encode()
        with patch('services.inference.runtime.Runtime') as runtime, patch(
                'services.inference.startup.create_trusted_app') as app:
            build_verified_app(policy, self.model)
            runtime.assert_called_once()
            self.assertEqual(runtime.call_args.args[1], str(self.model))
            runtime.return_value.start.assert_not_called()
            app.assert_called_once_with(policy, runtime.return_value)

    def test_changed_missing_and_unexpected_files_rejected(self):
        file = self.model / 'model.safetensors'
        for content in [b'x'*len(self.content), b'x', b'']:
            file.write_bytes(content)
            with self.assertRaisesRegex(ValueError, '^invalid_model_artifacts$'):
                artifacts.verify_snapshot(self.model)
        file.unlink()
        with self.assertRaises(ValueError):
            artifacts.verify_snapshot(self.model)
        file.write_bytes(self.content)
        extra = self.model / 'unexpected.py'
        extra.write_text('fixture')
        with self.assertRaises(ValueError):
            artifacts.verify_snapshot(self.model)
        extra.unlink()
        extra.mkdir()
        with self.assertRaises(ValueError):
            artifacts.verify_snapshot(self.model)

    def test_unsafe_manifest_and_wrong_revision_rejected(self):
        original = json.loads(json.dumps(self.manifest))
        for name in ['../escape', '/absolute', 'C:\\escape', '.', 'a/b']:
            self.manifest['artifacts'][0]['file'] = name
            self.save()
            with self.assertRaises(ValueError):
                artifacts.verify_snapshot(self.model)
        self.manifest = original
        self.manifest['revision'] = 'wrong'
        self.save()
        with self.assertRaises(ValueError):
            artifacts.verify_snapshot(self.model)
        self.path.write_bytes(b'{"model":1,"model":2}')
        with self.assertRaises(ValueError):
            artifacts.verify_snapshot(self.model)

    def test_hash_deadline_and_bad_policy_prevent_runtime(self):
        with patch('services.inference.artifacts.time.monotonic', side_effect=[0,31]):
            with self.assertRaises(ValueError):
                artifacts.verify_snapshot(self.model)
        with patch('services.inference.runtime.Runtime') as runtime:
            with self.assertRaises(ValueError):
                build_verified_app(b'{}', self.model)
            runtime.assert_not_called()

    def test_symlink_rejected(self):
        target = self.model / 'model.safetensors'
        target.unlink()
        source = self.root / 'source'
        source.write_bytes(self.content)
        try:
            target.symlink_to(source)
        except OSError:
            self.skipTest('host requires symlink privilege; Linux check required')
        with self.assertRaises(ValueError):
            artifacts.verify_snapshot(self.model)


if __name__ == '__main__':
    unittest.main()
