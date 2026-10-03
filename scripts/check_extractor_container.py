"""Smoke checks for the network-disabled extractor. Requires a built Docker image."""
import json
from pathlib import Path
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
COMMAND = ['docker', 'compose', '-f', 'compose.extraction.yaml', 'run', '--rm', '-T']


def execute(args, payload=None, timeout=60, command=None):
    name = 'gather-smoke-' + uuid.uuid4().hex
    process = subprocess.Popen((command or COMMAND) + ['--name', name] + args,
                               cwd=ROOT, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, _ = process.communicate(input=payload, timeout=timeout)
    finally:
        # On Windows, communicate after killing Compose can wait on inherited
        # pipes. Remove the container before draining or closing those pipes.
        if process.poll() is None:
            process.kill()
        try:
            cleanup = subprocess.run(['docker', 'rm', '-f', name], cwd=ROOT,
                                     capture_output=True, timeout=30)
            if cleanup.returncode and b'No such container' not in cleanup.stderr:
                raise RuntimeError('Smoke container cleanup failed; inspect Docker locally')
        finally:
            process.wait(timeout=10)
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()
    if process.returncode:
        raise RuntimeError('Container smoke command failed; inspect Docker locally')
    return stdout


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
    probe = '''import errno, importlib.metadata as m, importlib.util, json, os, pathlib, re, socket, subprocess, sysconfig
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
installed = {normalize(d.metadata['Name']): d.version for d in m.distributions()}
assert installed == locked, 'installed environment differs from lock'
assert importlib.util.find_spec('pip') is None
assert importlib.util.find_spec('ensurepip') is None
assert not list(pathlib.Path(sysconfig.get_path('purelib')).glob('pip*'))
for name, version in {'openssl':'3.5.7-1~deb13u3', 'libssl3t64':'3.5.7-1~deb13u3',
                      'openssl-provider-legacy':'3.5.7-1~deb13u3',
                      'libpcre2-8-0':'10.46-1~deb13u3'}.items():
    actual = subprocess.check_output(['dpkg-query', '-W', '-f=${Version}', name]).decode()
    assert actual == version, (name, actual)
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
    # The installer remains a developer-only build target, absent from runtime.
    installer_check = '''import importlib.metadata as m, pathlib
bootstrap = pathlib.Path('/app/requirements-bootstrap.lock').read_text()
assert f"pip=={m.version('pip')} --hash=sha256:" in bootstrap
'''
    print(execute(['--entrypoint', 'python', 'gather-extraction-installer', '-c',
                   installer_check + hash_probe], command=[
                       'docker', 'run', '--rm', '--network', 'none', '--read-only',
                       '--user', '65532:65532', '--cap-drop', 'ALL',
                       '--security-opt', 'no-new-privileges:true', '--memory', '1g',
                       '--cpus', '1', '--pids-limit', '64',
                       '--tmpfs', '/tmp:size=67108864,mode=1777']).decode().strip())
    started = time.monotonic()
    try:
        execute(['--entrypoint', 'python', 'extractor', '-c',
                 'import time; time.sleep(120)'], timeout=3)
    except subprocess.TimeoutExpired:
        assert time.monotonic() - started < 20, 'Timeout cleanup exceeded its smoke budget'
        print('PASS: timed-out Docker job cleaned up.')
    else:
        raise AssertionError('Timeout was not enforced')
    print('PASS: sample/error jobs, exact locked packages, non-root user, read-only app, unreachable external network, excluded personal paths.')
    print(json.dumps(versions))


if __name__ == '__main__':
    main()
