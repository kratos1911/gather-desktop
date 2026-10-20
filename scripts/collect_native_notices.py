"""Collect hash-verified crate notices declared by the exact serving wheel SBOMs.

Downloads source archives only; never extracts paths, installs or executes them.
Missing notices remain explicit review gaps, not silently accepted licences.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
import urllib.request
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 32 * 1024 * 1024


def archive_notices(content, expected):
    if hashlib.sha256(content).hexdigest() != expected:
        raise ValueError('crate_hash_mismatch')
    notices = []
    with tarfile.open(fileobj=io.BytesIO(content), mode='r:gz') as archive:
        for item in archive:
            name = PurePosixPath(item.name).name
            if not item.isfile() or not re.match(r'(?i)^(licen[cs]e|notice|copying|copyright|unlicense)([._-].*)?$', name):
                continue
            if item.size > 2*1024*1024 or len(notices) >= 300:
                raise ValueError('notice_limit')
            value = archive.extractfile(item).read()
            notices.append({'path': item.name, 'sha256': hashlib.sha256(value).hexdigest(),
                            'text': value.decode('utf-8')})
    return notices


def main():
    if ROOT.drive.upper() != 'D:':
        raise ValueError('D_drive_required')
    out = ROOT/'output/native-notices'
    cache = out/'crates'
    cache.mkdir(parents=True, exist_ok=True)
    inventory = json.loads((ROOT/'tests/inference/results/license-inventory-20261018.json').read_text())
    locked = {r['wheel']:r['sha256'] for r in inventory['wheels']}
    crates, local, sboms = {}, [], []
    for wheel in sorted((ROOT/'output/inference-auth/wheels').glob('*.whl')):
        with ZipFile(wheel) as archive:
            names = [n for n in archive.namelist() if '/sboms/' in n and n.endswith('.json')]
            if not names:
                continue
            if hashlib.sha256(wheel.read_bytes()).hexdigest() != locked.get(wheel.name):
                raise ValueError('wheel_hash_mismatch')
            for name in names:
                raw = archive.read(name)
                data = json.loads(raw)
                sboms.append({'wheel':wheel.name, 'path':name, 'sha256':hashlib.sha256(raw).hexdigest()})
                for c in data.get('components', []):
                    if not c.get('purl','').startswith('pkg:cargo/'):
                        continue
                    sha = next((h['content'] for h in c.get('hashes',[]) if h['alg']=='SHA-256'),None)
                    row = {k:c.get(k) for k in ('name','version','purl','licenses')}
                    if not sha:
                        local.append({'wheel':wheel.name, **row})
                        continue
                    if (not re.fullmatch(r'[a-zA-Z0-9_-]+',c['name'])
                            or not re.fullmatch(r'[a-zA-Z0-9.+_-]+',c['version'])
                            or not re.fullmatch(r'[a-f0-9]{64}',sha)):
                        raise ValueError('invalid_crate_identity')
                    key = (c['name'],c['version'])
                    if key in crates and crates[key]['sha256'] != sha:
                        raise ValueError('conflicting_crate_hash')
                    crates[key] = {**row, 'sha256':sha}
    def collect(row):
        row = dict(row)
        try:
            name = row['name']+'-'+row['version']+'.crate'
            path = cache/name
            row['url'] = 'https://static.crates.io/crates/'+row['name']+'/'+name
            if path.exists():
                if path.stat().st_size > LIMIT:
                    raise ValueError('archive_limit')
                content = path.read_bytes()
            else:
                with urllib.request.urlopen(row['url'], timeout=20) as response:
                    content = response.read(LIMIT+1)
                if len(content)>LIMIT:
                    raise ValueError('archive_limit')
            row['notices'] = archive_notices(content,row['sha256'])
            if not path.exists():
                path.write_bytes(content)
            row['status'] = 'collected' if row['notices'] else 'missing_notice'
        except Exception as error:
            row['status'] = 'unresolved'
            row['error'] = type(error).__name__
        return row
    records=[]
    supplement_root = ROOT/'services/inference/licenses/native-source-supplements'
    supplemental = json.loads((supplement_root/'provenance.json').read_text())
    supplements = {}
    for item in supplemental['files']:
        path = (supplement_root/item['path']).resolve()
        if not path.is_relative_to(supplement_root.resolve()):
            raise ValueError('unsafe_notice_path')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=item['sha256']:
            raise ValueError('supplement_hash_mismatch')
        supplements.setdefault(item['crate'],[]).append({**item,'text':data.decode('utf-8')})
    with ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(collect,sorted(crates.values(),key=lambda r:(r['name'],r['version']))):
            if row['status']=='missing_notice' and row['name']+'-'+row['version'] in supplements:
                row['notices']=supplements[row['name']+'-'+row['version']]
                row['status']='collected_from_pinned_upstream'
            records.append(row)
            if len(records)%50==0:
                print(f'Collected {len(records)}/{len(crates)} source inventories',flush=True)
    result={'scope':'All declared cargo components, including potentially non-runtime targets; not legal clearance',
            'sboms':sboms,'crates':records,'local_components':local,
            'unresolved_crates':[{'name':r['name'],'version':r['version'],'status':r['status']} for r in records if not r['status'].startswith('collected')]}
    target=out/'bundle.json'
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'crates':len(records),'unresolved':result['unresolved_crates'],
                      'local_components':len(local),'bundle_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))


if __name__=='__main__':
    main()
