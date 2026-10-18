"""Download only reviewed Debian source files to the project's D: output area."""
import hashlib
from pathlib import Path
import urllib.request

from services.inference.zlib.build import SOURCES

ROOT = Path(__file__).resolve().parents[1]


def main():
    if ROOT.drive.upper() != 'D:':
        raise SystemExit('Source artifacts must remain on D:')
    output = ROOT/'output/zlib-review'
    output.mkdir(parents=True, exist_ok=True)
    for name, sha in SOURCES.items():
        destination = output/name
        if destination.exists():
            if hashlib.sha256(destination.read_bytes()).hexdigest() != sha:
                raise ValueError('Existing source hash mismatch; not overwriting')
            continue
        remote = 'zlib_1.3.dfsg+really1.3.1-1.dsc' if name == 'source.dsc' else name
        with urllib.request.urlopen('https://deb.debian.org/debian/pool/main/z/zlib/'+remote, timeout=30) as response:
            content = response.read(2_000_001)
        if len(content) > 2_000_000 or hashlib.sha256(content).hexdigest() != sha:
            raise ValueError('Downloaded source hash mismatch')
        destination.write_bytes(content)
    print('Reviewed source files verified on D:')


if __name__ == '__main__':
    main()
