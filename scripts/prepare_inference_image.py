"""Stage only reviewed inference code/wheels and materialize a verified model on D:."""

import argparse
import email
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from services.inference.runtime import MODEL, REVISION

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "output/inference-patched"


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def prepare(build=BUILD, update_lock=False):
    if ROOT.drive.upper() != "D:":
        raise SystemExit("Build/model staging must be on D:.")
    build = build.resolve()
    if not build.is_relative_to(ROOT / 'output'):
        raise ValueError('Build context must stay in the D: output directory')
    wheels = sorted((build / "wheels").glob("*.whl"))
    if not wheels:
        raise SystemExit("Download the locked Linux CPU wheels first.")
    records = {}
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as archive:
            metadata = [name for name in archive.namelist()
                        if name.count('/') == 1 and name.endswith('.dist-info/METADATA')]
            if len(metadata) != 1:
                raise ValueError("Invalid wheel metadata")
            data = email.message_from_bytes(archive.read(metadata[0]))
        name = data['Name'].lower().replace('_', '-')
        if name in records:
            raise ValueError("Duplicate distribution in wheelhouse")
        records[name] = f"{name}=={data['Version']} --hash=sha256:{digest(wheel)}"
    lock = ROOT / "services/inference/requirements.lock"
    content = "# Linux x86_64 CPython 3.12; torch from official CPU index, others PyPI.\n" + '\n'.join(records[name] for name in sorted(records)) + '\n'
    # Regeneration must be deliberate: a changed wheelhouse cannot silently rewrite a lock.
    if lock.exists() and lock.read_text() != content and not update_lock:
        raise ValueError("Wheelhouse differs from reviewed lock")
    lock.write_text(content, encoding="utf-8")
    shutil.copyfile(lock, build / "requirements.lock")
    shutil.copyfile(ROOT / "services/inference/Dockerfile", build / "Dockerfile")
    target = build / "services/inference"
    target.mkdir(parents=True, exist_ok=True)
    for name in ("runtime.py", "qwen.py", "stream.py", "chunking.py"):
        shutil.copyfile(ROOT / "services/inference" / name, target / name)
    # BuildKit sees only this allowlist even if output contains older artifacts.
    (build / '.dockerignore').write_text('**\n!Dockerfile\n!requirements.lock\n!wheels/\n!wheels/*.whl\n!services/\n!services/inference/\n!services/inference/*.py\n')
    manifest = json.loads((ROOT / "output/model-benchmark/qwen-download.json").read_text())
    if (manifest['model'], manifest['revision'], manifest['status']) != (MODEL, REVISION, 'verified'):
        raise ValueError("Pinned verified model required")
    snapshot = Path(manifest['snapshot']).resolve()
    source_root = (ROOT / 'output/model-benchmark').resolve()
    model = ROOT / 'output/inference-model'
    model.mkdir(parents=True, exist_ok=True)
    for artifact in manifest['artifacts']:
        relative = Path(artifact['file'])
        source, destination = (snapshot / relative).resolve(), (model / relative).resolve()
        if not source.is_relative_to(source_root) or not destination.is_relative_to(model):
            raise ValueError("Unsafe model artifact path")
        if digest(source) != artifact['sha256']:
            raise ValueError("Source model hash mismatch")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists() or digest(destination) != artifact['sha256']:
            shutil.copyfile(source, destination)
        if digest(destination) != artifact['sha256']:
            raise ValueError("Exported model hash mismatch")
    print(f"Staged {len(wheels)} hash-locked wheels and verified model; no HF credentials copied.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-dir', type=Path, default=BUILD)
    parser.add_argument('--update-lock', action='store_true')
    options = parser.parse_args()
    prepare(options.build_dir, options.update_lock)
