"""Check exact package versions against PyPI's public advisory feed.

No installs or imports of audited packages. This does not scan OS packages or
detect unpublished vulnerabilities. Lookup errors are never a clean result.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def check(package):
    name, version = package['name'], package['version']
    url = f'https://pypi.org/pypi/{name}/{version}/json'
    try:
        request = Request(url, headers={'User-Agent': 'Gather-dependency-review/1'})
        with urlopen(request, timeout=30) as response:
            data = json.load(response)
        if not isinstance(data.get('vulnerabilities'), list):
            raise ValueError('Missing advisory response')
        return {'name': name, 'version': version, 'source': url,
                'vulnerabilities': data['vulnerabilities']}
    except Exception as error:
        return {'name': name, 'version': version, 'source': url,
                'error': type(error).__name__}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date', required=True, help='Review date YYYY-MM-DD')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    inventory = ROOT / 'services/worker/extraction-packages.json'
    raw = inventory.read_bytes()
    packages = json.loads(raw)['packages']
    bootstrap = (ROOT / 'services/worker/requirements-bootstrap.lock').read_bytes()
    pins = re.findall(r'^pip==([\w.]+) --hash=sha256:[a-f0-9]{64}$',
                      '\n'.join(bootstrap.decode().splitlines()), re.M)
    if len(pins) != 1:
        raise ValueError('Expected exactly one hash-pinned bootstrap pip')
    packages = packages + [{'name': 'pip', 'version': pins[0]}]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(check, packages))
    errors = [r for r in results if 'error' in r]
    affected = [r for r in results if r.get('vulnerabilities')]
    report = {'date': args.date, 'inventory_sha256': hashlib.sha256(raw).hexdigest(),
              'bootstrap_lock_sha256': hashlib.sha256(bootstrap).hexdigest(),
              'scope': 'PyPI advisory feed only; OS/browser binaries not scanned',
              'packages_checked': len(results), 'lookup_errors': len(errors),
              'affected_packages': len(affected), 'results': results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'{len(results)} packages checked; {len(errors)} lookup errors; {len(affected)} affected packages.')
    for item in affected:
        print(item['name'], item['version'], [v['id'] for v in item['vulnerabilities']])
    raise SystemExit(2 if errors else 1 if affected else 0)


if __name__ == '__main__':
    main()
