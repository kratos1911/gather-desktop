import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from scripts.collect_native_notices import archive_notices
from scripts.prepare_release_image import verify_native_bundle, ROOT


class ReleasePackagingTests(unittest.TestCase):
    def archive(self, name='fixture/LICENSE', content=b'fixture notice'):
        stream=io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w:gz') as archive:
            member=tarfile.TarInfo(name);member.size=len(content)
            archive.addfile(member,io.BytesIO(content))
        return stream.getvalue()

    def test_verified_notice_bytes_preserved(self):
        raw=self.archive()
        result=archive_notices(raw,hashlib.sha256(raw).hexdigest())
        self.assertEqual(result[0]['text'],'fixture notice')
        self.assertEqual(result[0]['sha256'],hashlib.sha256(b'fixture notice').hexdigest())

    def test_wrong_source_hash_rejected(self):
        with self.assertRaisesRegex(ValueError,'crate_hash_mismatch'):
            archive_notices(self.archive(),'0'*64)

    def test_missing_notice_remains_empty(self):
        raw=self.archive('fixture/src/lib.rs')
        self.assertEqual(archive_notices(raw,hashlib.sha256(raw).hexdigest()),[])

    def test_unreviewed_or_incomplete_bundle_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'output') as temp:
            path=Path(temp)/'bundle.json'
            value={'crates':[{}],'unresolved_crates':[]}
            raw=json.dumps(value).encode();path.write_bytes(raw)
            policy={'native_bundle_sha256':hashlib.sha256(raw).hexdigest(),'native_crates':1}
            self.assertEqual(verify_native_bundle(path,policy),raw)
            path.write_bytes(raw+b' ')
            with self.assertRaisesRegex(ValueError,'unreviewed'):
                verify_native_bundle(path,policy)
            value['unresolved_crates']=['missing'];raw=json.dumps(value).encode()
            path.write_bytes(raw);policy['native_bundle_sha256']=hashlib.sha256(raw).hexdigest()
            with self.assertRaisesRegex(ValueError,'incomplete'):
                verify_native_bundle(path,policy)
