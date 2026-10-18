import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from scripts.inference_notices import collect, ROOT


class NoticeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'output')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.wheel = self.root / 'fixture.whl'
        with ZipFile(self.wheel, 'w') as archive:
            archive.writestr('fixture.dist-info/licenses/LICENSE', 'Retain this notice\n')
        self.lock = self.root / 'requirements.lock'
        self.lock.write_text('fixture==1 --hash=sha256:' + hashlib.sha256(self.wheel.read_bytes()).hexdigest())

    def test_preserves_notice_and_hash(self):
        result = collect(self.root, self.lock, self.root / 'absent')
        self.assertEqual(result['wheels'][0]['notices'][0]['text'], 'Retain this notice\n')

    def test_modified_wheel_rejected(self):
        with self.wheel.open('ab') as stream:
            stream.write(b'changed')
        with self.assertRaisesRegex(ValueError, 'Unreviewed'):
            collect(self.root, self.lock)

    def test_missing_wheel_rejected(self):
        self.wheel.unlink()
        with self.assertRaisesRegex(ValueError, 'Missing'):
            collect(self.root, self.lock)

    def test_missing_supplement_rejected(self):
        target = self.root / 'supplements/component'
        target.mkdir(parents=True)
        (target / 'provenance.json').write_text('{"files":[{"path":"LICENSE"}]}')
        with self.assertRaises(FileNotFoundError):
            collect(self.root, self.lock, target.parent)

    def test_changed_or_escaping_supplement_rejected(self):
        target = self.root / 'supplements/component'
        target.mkdir(parents=True)
        (target / 'LICENSE').write_text('changed')
        manifest = target / 'provenance.json'
        manifest.write_text(json.dumps({'files': [{'path': 'LICENSE', 'sha256': '0' * 64}]}))
        with self.assertRaisesRegex(ValueError, 'Changed supplemental'):
            collect(self.root, self.lock, target.parent)
        manifest.write_text(json.dumps({'files': [{'path': '../../outside'}]}))
        with self.assertRaisesRegex(ValueError, 'Unsafe supplemental'):
            collect(self.root, self.lock, target.parent)


if __name__ == '__main__':
    unittest.main()
