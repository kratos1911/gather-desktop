"""Real Docker adversarial checks using synthetic code/data only.

Run after building the extraction runtime. Test subclasses replace the fixed
command in trusted code; job payloads cannot choose programs in DockerJobRunner.
"""
import json
from pathlib import Path
import subprocess
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.worker.supervisor import DockerJobRunner, WorkerError


def fixture_runner(image, source):
    class FixtureRunner(DockerJobRunner):
        _COMMAND = ('python', '-c', source)
    return FixtureRunner(image)


def expect_error(runner, code, **kwargs):
    started = time.monotonic()
    try:
        runner.run(b'', **kwargs)
    except WorkerError as error:
        assert str(error) == code, (str(error), code)
    else:
        raise AssertionError('Expected job failure')
    assert time.monotonic() - started < 20, 'Cleanup exceeded smoke budget'
    print('PASS:', code, flush=True)


def main():
    image = subprocess.check_output([
        'docker', 'image', 'inspect', 'gather-extraction-extractor', '--format', '{{.Id}}'
    ], text=True, timeout=15).strip()
    runner = DockerJobRunner(image)
    job = {'backend': 'crawl4ai', 'source_id': 'supervisor-fixture',
           'url': 'https://example.com', 'backend_version': 'fixture',
           'fetched_at': '2026-10-03T00:00:00Z',
           'result': {'success': True, 'status_code': 200,
                      'url': 'https://example.com', 'markdown': 'Synthetic note'}}
    response = runner.run(json.dumps(job).encode())
    assert response['status'] == 'processed'
    assert response['document']['semantic_ready'] is False
    assert runner.run(b'not-json')['status'] == 'error'
    print('PASS: bounded successful and invalid jobs', flush=True)

    expect_error(fixture_runner(image, 'import time; time.sleep(120)'),
                 'WORKER_TIMEOUT', timeout=.5)
    expect_error(fixture_runner(image, 'import sys; sys.stdout.write("x"*3000000)'),
                 'WORKER_OUTPUT_LIMIT')
    expect_error(fixture_runner(image, 'import sys; sys.stderr.write("x"*20000)'),
                 'WORKER_OUTPUT_LIMIT')
    expect_error(fixture_runner(image, 'print("not-json")'), 'WORKER_INVALID_RESULT')
    expect_error(fixture_runner(image, 'raise RuntimeError("fixture-secret")'), 'WORKER_FAILED')
    cancelled = threading.Event()
    timer = threading.Timer(1, cancelled.set)
    timer.start()
    try:
        expect_error(fixture_runner(image, 'import time; time.sleep(120)'),
                     'WORKER_CANCELLED', cancel=cancelled)
    finally:
        timer.cancel()

    source = '''import errno, json, os, socket, pathlib
assert os.getuid() == 65532
assert not os.path.exists('/var/run/docker.sock')
assert not os.path.exists('/app/.env')
limits = pathlib.Path('/sys/fs/cgroup')
assert (limits / 'memory.max').read_text().strip() == '1073741824'
assert (limits / 'memory.swap.max').read_text().strip() == '0'
assert (limits / 'pids.max').read_text().strip() == '64'
quota, period = (limits / 'cpu.max').read_text().split()
assert int(quota) == int(period)
try:
    open('/app/forbidden', 'w').close()
except OSError as error:
    assert error.errno in (errno.EROFS, errno.EACCES)
else:
    raise AssertionError('Writable application path')
for address in ['1.1.1.1', '169.254.169.254', '10.0.0.1']:
    with socket.socket() as sock:
        sock.settimeout(.5)
        try:
            sock.connect((address, 80))
        except OSError as error:
            assert error.errno in (errno.ENETUNREACH, errno.EHOSTUNREACH)
        else:
            raise AssertionError('Direct egress bypass')
print(json.dumps({'status':'processed'}))
'''
    assert fixture_runner(image, source).run(b'')['status'] == 'processed'
    # A successful job after failures proves the local concurrency slot recovers.
    assert runner.run(b'not-json')['status'] == 'error'
    leftovers = subprocess.check_output([
        'docker', 'ps', '-a', '--filter', 'name=gather-job-', '--format', '{{.Names}}'
    ], text=True, timeout=15).strip()
    assert not leftovers, 'Supervisor containers remain; inspect Docker locally'
    print('PASS: direct egress blocked, read-only/non-root, no socket/secrets, no leftover jobs', flush=True)


if __name__ == '__main__':
    main()
