"""Install only the reviewed local Debian backport into the Gather image."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parent
manifest = json.loads((root/'artifact.json').read_text())
package = root/'zlib1g-gather1.deb'
if hashlib.sha256(package.read_bytes()).hexdigest() != manifest['package_sha256']:
    raise SystemExit('zlib package hash mismatch')
query = ['dpkg-query', '-W', '-f=${Version}', 'zlib1g:amd64']
previous = subprocess.check_output(query, text=True)
if previous != manifest['replaces']:
    raise SystemExit('Unreviewed base zlib version')
subprocess.run(['dpkg', '-i', str(package)], check=True)
if subprocess.check_output(query, text=True) != manifest['version']:
    raise SystemExit('Installed zlib version mismatch')
shutil.copyfile(root/'artifact.json', '/usr/share/doc/zlib1g/gather-backport.json')
shutil.copyfile(root/'CVE-2026-85091.patch', '/usr/share/doc/zlib1g/gather-backport.patch')
