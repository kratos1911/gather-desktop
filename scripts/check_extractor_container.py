"""Smoke checks for the network-disabled extractor. Requires a built Docker image."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMMAND = ['docker', 'compose', '-f', 'compose.extraction.yaml', 'run', '--rm', '-T']


def execute(args, payload=None):
    result = subprocess.run(COMMAND + args, cwd=ROOT, input=payload,
                            capture_output=True, timeout=60)
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
    probe = '''import errno, importlib.metadata as m, json, os, socket
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
print(json.dumps(versions))
'''
    versions = json.loads(execute(['--entrypoint', 'python', 'extractor', '-c', probe]))
    print('PASS: sample/error jobs, non-root user, read-only app, unreachable external network, excluded personal paths.')
    print(json.dumps(versions))


if __name__ == '__main__':
    main()
