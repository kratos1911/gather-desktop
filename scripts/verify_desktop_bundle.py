"""Read-only identity check for Gather's native executable inside an NSIS install."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MARKER = b"__TAURI_BUNDLE_TYPE_VAR_UNK"
NSIS_MARKER = b"__TAURI_BUNDLE_TYPE_VAR_NSS"
MAX_BYTES = 64 * 1024 * 1024


def verify_bytes(source, installed, expected_sha256):
    """Accept exactly Tauri's NSIS marker patch; every other byte must match."""
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise ValueError("invalid_verified_source_hash")
    if not 0 < len(source) <= MAX_BYTES or not 0 < len(installed) <= MAX_BYTES:
        raise ValueError("executable_size_limit")
    source_hash = hashlib.sha256(source).hexdigest()
    if source_hash != expected_sha256.lower():
        raise ValueError("source_differs_from_verified_candidate")
    if not source.startswith(b"MZ") or source.count(MARKER) != 1:
        raise ValueError("unexpected_tauri_bundle_marker")
    expected = source.replace(MARKER, NSIS_MARKER, 1)
    if installed != expected:
        raise ValueError("installed_executable_mismatch")
    return {
        "verified": True,
        "source_sha256": source_hash,
        "installed_sha256": hashlib.sha256(installed).hexdigest(),
        "allowed_change": "Tauri NSIS bundle marker UNK -> NSS; all other bytes identical",
        "signing_or_clean_machine_acceptance": False,
    }


def read_binary(path):
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("executable_size_limit")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installed", type=Path, required=True)
    args = parser.parse_args()
    proof = json.loads((ROOT / "output/private-desktop/verification.json").read_text(encoding="utf-8-sig"))
    source = ROOT / "output/private-desktop/Gather-Private-Pilot.exe"
    print(json.dumps(verify_bytes(read_binary(source), read_binary(args.installed), proof["sha256"])))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError):
        raise SystemExit("Desktop bundle verification failed. No executable was run or changed.") from None
