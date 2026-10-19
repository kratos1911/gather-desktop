"""Fail closed if the reviewed backport is absent or changed."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def stage(build, root=ROOT):
    policy = root/'services/inference/zlib'
    package = root/'output/zlib-review/zlib1g-gather1.deb'
    patch = policy/'CVE-2026-85091.patch'
    # Read every input before writing anything, and copy the exact checked bytes.
    sources = {path: path.read_bytes() for path in
               (package, patch, policy/'artifact.json', policy/'install.py')}
    manifest = json.loads(sources[policy/'artifact.json'].decode('utf-8'))
    for path, key in ((package, 'package_sha256'), (patch, 'patch_sha256')):
        if hashlib.sha256(sources[path]).hexdigest() != manifest[key]:
            raise ValueError('Unreviewed zlib artifact')
    target = build/'zlib-patch'
    target.mkdir(exist_ok=True)
    for path, content in sources.items():
        (target/path.name).write_bytes(content)
