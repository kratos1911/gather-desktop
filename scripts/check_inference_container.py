"""Run only a uniquely named Gather container; never change other workloads."""

import argparse
import json
import math
import subprocess
import time
import uuid

from scripts.prepare_inference_image import ROOT, digest
from services.inference.runtime import MODEL, REVISION


def profile_requests(profile):
    def document(tokens):
        # Verified with the pinned AutoTokenizer: one special token is appended.
        return {'role': 'document', 'texts': ['x' + ' x' * (tokens - 2)]}
    if profile == 'long':
        return [document(n) for n in (512, 1024, 2048)], [None] * 3
    if profile == 'batch':
        return [{'role': 'document', 'texts': document(2048)['texts'] * 2}], [None]
    if profile == 'limits':
        return [document(2049), {'role': 'document', 'texts': document(1400)['texts'] * 3},
                document(16)], ['token_limit', 'token_limit', None]
    if profile == 'sustained':
        return [{'role': 'query', 'texts': [f'Find the fictional museum record number {i}.']}
                for i in range(50)], [None] * 50
    if profile == 'compatibility':
        pairs = [('document', 'The fictional museum opens at nine on Tuesday.'),
                 ('query', 'When does the museum open?'),
                 ('document', 'Archive code AX-170: the blue folder contains lunar maps.'),
                 ('query', 'Where are the lunar maps?'),
                 ('document', 'संग्रहालय मंगलवार को खुलता है। Photos: café, 東京, 🙂.'),
                 ('query', 'Find multilingual museum notes.')]
        return [{'role': role, 'texts': [text]} for role, text in pairs], [None] * len(pairs)
    if profile == 'chunks':
        from tokenizers import Tokenizer
        from services.inference.chunking import chunk_document
        tokenizer = Tokenizer.from_file(str(ROOT / 'output/inference-model/tokenizer.json'))
        text = ('Museum entry: the blue room keeps lunar maps. Archive code AX-170.\n\n' * 70
                + 'संग्रहालय मंगलवार को खुलता है। Photos: café, 東京, 🙂.\n' * 20)
        chunks = chunk_document(text, lambda value: len(tokenizer.encode(value).ids))
        return [{'role': 'document', 'texts': [chunk['text']]} for chunk in chunks], [None] * len(chunks)
    requests = [('document', 'The fictional museum opens at nine on Tuesday.'),
                ('query', 'When does the museum open?')] + [('query', 'When does the museum open?')] * 8
    return [{'role': role, 'texts': [text]} for role, text in requests], [None] * len(requests)


def review_rows(rows, requests, expected):
    outcomes = []
    replies = [row for row in rows if 'result' in row or 'error' in row]
    for index, (request, error) in enumerate(zip(requests, expected)):
        if index >= len(replies):
            outcomes.append({'index': index, 'passed': False, 'error': 'not_executed'})
            continue
        row = replies[index]
        if 'error' in row:
            outcomes.append({'index': index, 'passed': row['error'] == error, 'error': row['error']})
            continue
        result = row['result']
        valid = error is None and (result.get('model'), result.get('revision'), result.get('dimensions')) == (MODEL, REVISION, 512)
        vectors = result.get('data', [])
        valid = valid and len(vectors) == len(request['texts'])
        for position, item in enumerate(vectors):
            vector = item.get('embedding', [])
            valid = valid and item.get('index') == position and len(vector) == 512
            valid = valid and all(type(v) in (float, int) and math.isfinite(v) for v in vector)
            valid = valid and abs(math.hypot(*vector) - 1) < 1e-6
        outcomes.append({'index': index, 'passed': bool(valid), 'seconds': row['seconds'],
                         'prompt_tokens': result.get('prompt_tokens')})
    return outcomes, len(replies) == len(requests) and all(item['passed'] for item in outcomes)


def command(*args):
    return subprocess.run(['docker', *args], check=True, capture_output=True, text=True, timeout=30).stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--controls', action='store_true')
    parser.add_argument('--profile', choices=['smoke', 'long', 'batch', 'limits', 'sustained', 'compatibility', 'chunks'], default='smoke')
    parser.add_argument('--candidate', action='store_true', help='Use the separate patched image and output directory')
    args = parser.parse_args()
    image_name = 'gather-inference:cpu-patched' if args.candidate else 'gather-inference:cpu-local'
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
                    '--mount', f'type=bind,source={ROOT / "scripts"},target=/app/scripts,readonly',
                    '--entrypoint', 'python', image_name,
                    '-m', 'unittest', 'discover', '-s', '/tests', '-v']
        payload = ''
    else:
        options += ['--mount', f'type=bind,source={model},target=/model,readonly', image_name]
        requests, expected = profile_requests(args.profile)
        payload = ''.join(json.dumps(request) + '\n' for request in requests)
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
        report = {'scope': 'synthetic control tests' if args.controls else 'real Qwen Linux CPU smoke; fictional inputs',
                  'image_id': config['Image'], 'wall_seconds': time.perf_counter() - started,
                  'cpu_limit': 2, 'memory_limit_bytes': memory, 'swap_extra_bytes': 0,
                  'network': 'none', 'nonroot': True, 'readonly': True, 'exit_code': state['ExitCode'],
                  'oom_killed': state['OOMKilled'], 'passed': not (process.returncode or state['ExitCode'] or state['OOMKilled'])}
        if args.controls:
            print(stderr)
        else:
            rows = [json.loads(line) for line in stdout.splitlines()]
            report['passed'] = report['passed'] and bool(rows) and rows[0].get('status') == 'ready'
            results = [row for row in rows if 'result' in row]
            outcomes, valid = review_rows(rows, requests, expected)
            report['passed'] = report['passed'] and valid
            if args.profile == 'smoke' and len(results) == len(requests):
                report['passed'] = report['passed'] and results[1]['result'] == results[-1]['result']
            report.update(model=MODEL, revision=REVISION, profile=args.profile, outcomes=outcomes,
                          startup_seconds=rows[0].get('startup_seconds') if rows else None,
                          request_seconds=[row['seconds'] for row in results],
                          container_peak_bytes=next((row['container_peak_bytes'] for row in rows if 'container_peak_bytes' in row), None))
        destination = ROOT / 'output/inference-results'
        if args.candidate:
            destination = destination / 'patched'
        destination.mkdir(parents=True, exist_ok=True)
        if not args.controls and args.profile == 'compatibility':
            # Synthetic-only diagnostic vectors stay ignored; never export user text.
            (destination / 'compatibility-vectors.json').write_text(json.dumps([r['result'] for r in results]))
        if not args.controls and args.profile == 'chunks':
            report['passed'] = report['passed'] and all(0 < row.get('prompt_tokens', 0) <= 512 for row in outcomes)
        filename = 'controls.json' if args.controls else ('qwen.json' if args.profile == 'smoke' else f'qwen-{args.profile}.json')
        (destination / filename).write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        if not report['passed']:
            raise SystemExit('Profile did not pass; retained failure evidence. Limits were not relaxed.')
    finally:
        command('rm', '-f', identifier)


if __name__ == '__main__':
    main()
