"""Fail closed if the reviewed backport is absent or changed."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def stage(build, root=ROOT):
    policy = root/'services/inference/zlib'
    manifest = json.loads((policy/'artifact.json').read_text(encoding='utf-8'))
    package = root/'output/zlib-review/zlib1g-gather1.deb'
    patch = policy/'CVE-2026-85091.patch'
    for path, key in ((package, 'package_sha256'), (patch, 'patch_sha256')):
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest[key]:
            raise ValueError('Unreviewed zlib artifact')
    target = build/'zlib-patch'
    target.mkdir(exist_ok=True)
    for path in (package, patch, policy/'artifact.json', policy/'install.py'):
        shutil.copyfile(path, target/path.name)
