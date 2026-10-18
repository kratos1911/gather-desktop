"""Collect exact locked wheel notices without extracting archive paths."""

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def collect(wheelhouse, lock, supplements=ROOT / 'services/inference/licenses'):
    hashes = re.findall(r'--hash=sha256:([a-f0-9]{64})', lock.read_text(encoding='utf-8'))
    if not hashes or len(set(hashes)) != len(hashes):
        raise ValueError('Invalid lock hashes')
    rows = []
    seen = set()
    for wheel in sorted(wheelhouse.glob('*.whl')):
        digest = hashlib.sha256()
        with wheel.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        value = digest.hexdigest()
        if value not in hashes or value in seen:
            raise ValueError('Unreviewed or duplicate wheel')
        seen.add(value)
        notices = []
        with ZipFile(wheel) as archive:
            for entry in archive.infolist():
                name = PurePosixPath(entry.filename).name.lower()
                if entry.is_dir() or not any(word in name for word in ('license', 'licence', 'copying', 'notice')):
                    continue
                if entry.file_size > 2 * 1024 * 1024:
                    raise ValueError('Oversized notice')
                data = archive.read(entry)
                notices.append({'path': entry.filename, 'sha256': hashlib.sha256(data).hexdigest(),
                                'text': data.decode('utf-8')})
        rows.append({'wheel': wheel.name, 'sha256': value, 'notices': notices})
    if seen != set(hashes):
        raise ValueError('Missing locked wheel')
    extra = []
    for manifest in sorted(supplements.glob('*/provenance.json')):
        record = json.loads(manifest.read_text(encoding='utf-8'))
        for item in record['files']:
            path = (manifest.parent / item['path']).resolve()
            if not path.is_relative_to(manifest.parent.resolve()):
                raise ValueError('Unsafe supplemental path')
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != item['sha256']:
                raise ValueError('Changed supplemental notice')
            extra.append({**item, 'project': record['project'], 'version': record['version'],
                          'text': data.decode('utf-8')})
    return {'scope': 'Retained wheel and supplemental upstream notices; not complete native/OS licence clearance',
            'wheels': rows, 'supplements': extra}
