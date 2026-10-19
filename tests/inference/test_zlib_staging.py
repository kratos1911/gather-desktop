import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from scripts.stage_zlib import stage, ROOT


class BackportStagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT/'output')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.policy = self.root/'services/inference/zlib'
        self.policy.mkdir(parents=True)
        self.package = self.root/'output/zlib-review/zlib1g-gather1.deb'
        self.package.parent.mkdir(parents=True)
        self.package.write_bytes(b'fixture, not a real package')
        patch = self.policy/'CVE-2026-85091.patch'
        patch.write_bytes(b'fixture patch')
        (self.policy/'install.py').write_text('# fixture')
        (self.policy/'artifact.json').write_text(json.dumps({
            'package_sha256': hashlib.sha256(self.package.read_bytes()).hexdigest(),
            'patch_sha256': hashlib.sha256(patch.read_bytes()).hexdigest()}))
        self.build = self.root/'build'
        self.build.mkdir()

    def test_exact_artifacts_staged(self):
        stage(self.build, self.root)
        self.assertEqual((self.build/'zlib-patch/zlib1g-gather1.deb').read_bytes(), self.package.read_bytes())

    def test_changed_package_rejected_before_copy(self):
        self.package.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Unreviewed'):
            stage(self.build, self.root)
        self.assertFalse((self.build/'zlib-patch').exists())

    def test_missing_package_rejected(self):
        self.package.unlink()
        with self.assertRaises(FileNotFoundError):
            stage(self.build, self.root)

    def test_changed_patch_rejected(self):
        (self.policy/'CVE-2026-85091.patch').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Unreviewed'):
            stage(self.build, self.root)

    def test_missing_patch_raises_before_directory_creation(self):
        (self.policy/'CVE-2026-85091.patch').unlink()
        with self.assertRaises(FileNotFoundError):
            stage(self.build, self.root)
        self.assertFalse((self.build/'zlib-patch').exists())

    def test_missing_installer_rejected_before_directory_creation(self):
        (self.policy/'install.py').unlink()
        with self.assertRaises(FileNotFoundError):
            stage(self.build, self.root)
        self.assertFalse((self.build/'zlib-patch').exists())

    def test_missing_manifest_rejected_before_directory_creation(self):
        (self.policy/'artifact.json').unlink()
        with self.assertRaises(FileNotFoundError):
            stage(self.build, self.root)
        self.assertFalse((self.build/'zlib-patch').exists())

    def test_invalid_input_preserves_existing_staging(self):
        stage(self.build, self.root)
        target = self.build/'zlib-patch'
        before = {p.name: p.read_bytes() for p in target.iterdir()}
        (self.policy/'install.py').unlink()
        with self.assertRaises(FileNotFoundError):
            stage(self.build, self.root)
        self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, before)
