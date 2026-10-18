"""Verify an operator-owned immutable model directory against the packaged pins."""
import hashlib
from pathlib import Path
import re
import stat
import time

from services.inference.runtime import MODEL, REVISION
from services.worker.service_transport import strict_json

MANIFEST = Path(__file__).with_name('model-manifest.json')


def _regular(path):
    info = path.lstat()
    return (stat.S_ISREG(info.st_mode) and not path.is_symlink()
            and not getattr(info, 'st_file_attributes', 0) & 1024)


def verify_snapshot(snapshot):
    """No download, credentials, recursive traversal, pickle or remote-code loading.

    Caller must keep the directory immutable/read-only through model lifetime.
    Hashing alone cannot prevent a privileged host modifying files afterward.
    """
    try:
        root = Path(snapshot)
        if not root.is_absolute() or root.is_symlink() or not root.is_dir():
            raise ValueError()
        if getattr(root.lstat(), 'st_file_attributes', 0) & 1024:
            raise ValueError()
        with MANIFEST.open('rb') as stream:
            raw = stream.read(65537)
        if len(raw) > 65536:
            raise ValueError()
        manifest = strict_json(raw)
        if (set(manifest) != {'model','revision','expected_bytes','artifacts'}
                or (manifest['model'], manifest['revision']) != (MODEL, REVISION)
                or type(manifest['expected_bytes']) is not int
                or not 0 < manifest['expected_bytes'] <= 2 * 1024**3
                or not isinstance(manifest['artifacts'], list)
                or not 1 <= len(manifest['artifacts']) <= 32):
            raise ValueError()
        expected = {}
        for item in manifest['artifacts']:
            if (not isinstance(item, dict) or set(item) != {'file','bytes','sha256'}
                    or not isinstance(item['file'], str)
                    or not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}', item['file'])
                    or item['file'] in expected or type(item['bytes']) is not int
                    or not 0 < item['bytes'] <= manifest['expected_bytes']
                    or not isinstance(item['sha256'], str)
                    or not re.fullmatch(r'[a-f0-9]{64}', item['sha256'])):
                raise ValueError()
            expected[item['file']] = item
        if sum(item['bytes'] for item in expected.values()) != manifest['expected_bytes']:
            raise ValueError()
        actual = set()
        for path in root.iterdir():
            if len(actual) >= 32 or not _regular(path):
                raise ValueError()
            actual.add(path.name)
        if actual != set(expected):
            raise ValueError()
        deadline = time.monotonic() + 30
        for name, item in expected.items():
            path = root / name
            if path.stat().st_size != item['bytes']:
                raise ValueError()
            digest = hashlib.sha256()
            total = 0
            with path.open('rb') as stream:
                while block := stream.read(1024 * 1024):
                    total += len(block)
                    if total > item['bytes'] or time.monotonic() >= deadline:
                        raise ValueError()
                    digest.update(block)
            if total != item['bytes'] or digest.hexdigest() != item['sha256']:
                raise ValueError()
        return root
    except Exception:
        raise ValueError('invalid_model_artifacts') from None
