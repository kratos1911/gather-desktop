"""Run only a uniquely named Gather container; never change other workloads."""

import argparse
import json
import math
import subprocess
import time
import uuid

from scripts.prepare_inference_image import ROOT, digest
from services.inference.runtime import MODEL, REVISION


def command(*args):
    return subprocess.run(['docker', *args], check=True, capture_output=True, text=True, timeout=30).stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--controls', action='store_true')
    args = parser.parse_args()
    memory = 512 * 1024**2 if args.controls else 5 * 1024**3
    model = ROOT / 'output/inference-model'
    if not args.controls:
        import psutil
        if psutil.virtual_memory().available < 4 * 1024**3:
            raise SystemExit('Real-model check paused: at least 4 GiB available RAM required.')
        manifest = json.loads((ROOT / 'output/model-benchmark/qwen-download.json').read_text())
        if (manifest['model'], manifest['revision'], manifest['status']) != (MODEL, REVISION, 'verified'):
            raise ValueError('Verified pinned manifest required')
        allowed = set()
        for artifact in manifest['artifacts']:
            path = (model / artifact['file']).resolve()
            if not path.is_relative_to(model) or digest(path) != artifact['sha256']:
                raise ValueError('Model integrity check failed')
            allowed.add(path)
        if {path.resolve() for path in model.rglob('*') if path.is_file()} != allowed:
            raise ValueError('Unexpected file in isolated model directory')
    name = 'gather-inference-' + uuid.uuid4().hex[:12]
    options = ['create', '--name', name, '--label', 'com.gather.purpose=inference-test',
               '--network', 'none', '--read-only', '--user', '65532:65532', '--cpus', '2',
               '--memory', str(memory), '--memory-swap', str(memory), '--pids-limit', '128',
               '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
               '--tmpfs', '/tmp:rw,noexec,nosuid,size=67108864', '--log-driver', 'none', '-i']
    if args.controls:
        options += ['--mount', f'type=bind,source={ROOT / "tests/inference"},target=/tests,readonly',
                    '--entrypoint', 'python', 'gather-inference:cpu-local',
                    '-m', 'unittest', 'discover', '-s', '/tests', '-v']
        payload = ''
    else:
        options += ['--mount', f'type=bind,source={model},target=/model,readonly', 'gather-inference:cpu-local']
        requests = [('document', 'The fictional museum opens at nine on Tuesday.'),
                    ('query', 'When does the museum open?')] + [('query', 'When does the museum open?')] * 8
        payload = ''.join(json.dumps({'role': role, 'texts': [text]}) + '\n' for role, text in requests)
    identifier = command(*options).strip()
    try:
        config = json.loads(command('inspect', identifier))[0]
        host = config['HostConfig']
        assert host['Memory'] == memory and host['MemorySwap'] == memory
        assert host['NanoCpus'] == 2000000000 and host['PidsLimit'] == 128
        assert host['NetworkMode'] == 'none' and host['ReadonlyRootfs']
        assert config['Config']['User'] == '65532:65532'
        assert 'ALL' in host['CapDrop'] and 'no-new-privileges' in host['SecurityOpt']
        assert all(not mount['RW'] for mount in config['Mounts'])
        started = time.perf_counter()
        process = subprocess.Popen(['docker', 'start', '-ai', identifier], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            stdout, stderr = process.communicate(payload, timeout=300)
        except subprocess.TimeoutExpired:
            command('kill', identifier)
            process.kill()
            process.communicate(timeout=10)
            raise RuntimeError('Container smoke deadline exceeded') from None
        state = json.loads(command('inspect', identifier))[0]['State']
        if process.returncode or state['ExitCode'] or state['OOMKilled']:
            raise RuntimeError(f"Container check failed: exit={state['ExitCode']}, OOM={state['OOMKilled']}")
        report = {'scope': 'synthetic control tests' if args.controls else 'real Qwen Linux CPU smoke; fictional inputs',
                  'image_id': config['Image'], 'wall_seconds': time.perf_counter() - started,
                  'cpu_limit': 2, 'memory_limit_bytes': memory, 'swap_extra_bytes': 0,
                  'network': 'none', 'nonroot': True, 'readonly': True, 'exit_code': state['ExitCode']}
        if args.controls:
            print(stderr)
        else:
            rows = [json.loads(line) for line in stdout.splitlines()]
            assert rows[0]['status'] == 'ready'
            results = [row for row in rows if 'result' in row]
            assert len(results) == len(requests)
            for row in results:
                result = row['result']
                assert (result['model'], result['revision'], result['dimensions']) == (MODEL, REVISION, 512)
                vector = result['data'][0]['embedding']
                assert len(vector) == 512 and abs(math.hypot(*vector) - 1) < 1e-6
            assert results[1]['result'] == results[-1]['result']
            report.update(model=MODEL, revision=REVISION, startup_seconds=rows[0]['startup_seconds'],
                          request_seconds=[row['seconds'] for row in results],
                          container_peak_bytes=rows[-1]['container_peak_bytes'])
        destination = ROOT / 'output/inference-results'
        destination.mkdir(exist_ok=True)
        (destination / ('controls.json' if args.controls else 'qwen.json')).write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
    finally:
        command('rm', '-f', identifier)


if __name__ == '__main__':
    main()
