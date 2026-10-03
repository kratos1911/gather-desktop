"""Smoke checks for the network-disabled extractor. Requires a built Docker image."""
import json
from pathlib import Path
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]
COMMAND = ['docker', 'compose', '-f', 'compose.extraction.yaml', 'run', '--rm', '-T']


def execute(args, payload=None, timeout=60):
    name = 'gather-smoke-' + uuid.uuid4().hex
    try:
        result = subprocess.run(COMMAND + ['--name', name] + args, cwd=ROOT,
                                input=payload, capture_output=True, timeout=timeout)
    finally:
        # Killing the Docker client alone does not reliably stop its container.
        cleanup = subprocess.run(['docker', 'rm', '-f', name], cwd=ROOT,
                                 capture_output=True, timeout=30)
        if cleanup.returncode and b'No such container' not in cleanup.stderr:
            raise RuntimeError('Smoke container cleanup failed; inspect Docker locally')
    if result.returncode:
        raise RuntimeError('Container smoke command failed; inspect Docker locally')
    return result.stdout


def main():
    job = {'backend': 'crawl4ai', 'source_id': 'smoke', 'url': 'https://example.com',
           'backend_version': 'fixture', 'fetched_at': '2026-10-01T00:00:00Z',
           'result': {'success': True, 'status_code': 200, 'url': 'https://example.com',
                      'markdown': 'Synthetic waterproof jacket note'}}
    response = json.loads(execute(['extractor'], json.dumps(job).encode()))
    assert response['status'] == 'processed'
    assert response['document']['fields']['page_text'] == job['result']['markdown']
    assert response['document']['semantic_ready'] is False
    assert json.loads(execute(['extractor'], b'not-json'))['status'] == 'error'
    probe = '''import errno, importlib.metadata as m, json, os, pathlib, re, socket
assert os.getuid() == 65532
try:
    open('/app/write-probe', 'w').close()
except OSError as e:
    assert e.errno in (errno.EROFS, errno.EACCES)
else:
    raise AssertionError('application directory writable')
with socket.socket() as s:
    s.settimeout(2)
    try:
        s.connect(('1.1.1.1', 443))
    except OSError as e:
        assert e.errno in (errno.ENETUNREACH, errno.EHOSTUNREACH), str(e)
    else:
        raise AssertionError('external network reachable')
assert not os.path.exists('/app/.env')
assert not os.path.exists('/app/data')
versions = {name:m.version(name) for name in ('crawl4ai','yt-dlp')}
assert versions == {'crawl4ai':'0.9.4','yt-dlp':'2026.8.19'}
normalize = lambda name: re.sub(r'[-_.]+', '-', name).lower()
locked = {}
for line in pathlib.Path('/app/requirements-extraction.lock').read_text().splitlines():
    if line and not line.startswith('#'):
        name, version = line.split()[0].split('==')
        locked[normalize(name)] = version
installed = {normalize(d.metadata['Name']): d.version for d in m.distributions()
             if normalize(d.metadata['Name']) != 'pip'}
assert installed == locked, 'installed environment differs from lock'
bootstrap = pathlib.Path('/app/requirements-bootstrap.lock').read_text()
assert f"pip=={m.version('pip')} --hash=sha256:" in bootstrap
print(json.dumps(versions))
'''
    versions = json.loads(execute(['--entrypoint', 'python', 'extractor', '-c', probe]))
    hash_probe = '''import hashlib, json, pathlib, subprocess, sys, tempfile, zipfile
with tempfile.TemporaryDirectory() as folder:
    root = pathlib.Path(folder)
    wheel = root / 'gather_hash_probe-0.0.0-py3-none-any.whl'
    with zipfile.ZipFile(wheel, 'w') as archive:
        archive.writestr('gather_hash_probe-0.0.0.dist-info/METADATA',
                         'Metadata-Version: 2.1\\nName: gather-hash-probe\\nVersion: 0.0.0\\n')
        archive.writestr('gather_hash_probe-0.0.0.dist-info/WHEEL',
                         'Wheel-Version: 1.0\\nRoot-Is-Purelib: true\\nTag: py3-none-any\\n')
        archive.writestr('gather_hash_probe-0.0.0.dist-info/RECORD', '')
    requirements = root / 'requirements.txt'
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    command = [sys.executable, '-m', 'pip', '--isolated', 'download',
               '--no-index', '--no-cache-dir', '--disable-pip-version-check',
               '--find-links', str(root), '--require-hashes', '--only-binary=:all:',
               '--dest', str(root / 'download'), '-r', str(requirements)]
    requirements.write_text('gather-hash-probe==0.0.0 --hash=sha256:' + '0'*64)
    rejected = subprocess.run(command, capture_output=True, timeout=20)
    assert rejected.returncode != 0
    assert b'DO NOT MATCH THE HASHES' in rejected.stderr, rejected.stderr
    requirements.write_text('gather-hash-probe==0.0.0 --hash=sha256:' + digest)
    accepted = subprocess.run(command, capture_output=True, timeout=20)
    assert accepted.returncode == 0, accepted.stderr
print(json.dumps({'hash_rejection': True, 'correct_hash_accepted': True}))
'''
    print(execute(['--entrypoint', 'python', 'extractor', '-c', hash_probe]).decode().strip())
    try:
        execute(['--entrypoint', 'python', 'extractor', '-c',
                 'import time; time.sleep(120)'], timeout=3)
    except subprocess.TimeoutExpired:
        print('PASS: timed-out Docker job cleaned up.')
    else:
        raise AssertionError('Timeout was not enforced')
    print('PASS: sample/error jobs, exact locked packages, non-root user, read-only app, unreachable external network, excluded personal paths.')
    print(json.dumps(versions))


if __name__ == '__main__':
    main()
