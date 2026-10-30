"""Stage a fresh allowlisted API image context on D:, with no credentials/data."""
import hashlib
import json
from pathlib import Path
import shutil
from urllib.request import urlopen
from uuid import uuid4
from services.worker.cloud_provider import pinned_token_counter

ROOT=Path(__file__).resolve().parents[1]
BASE='asia-south1-docker.pkg.dev/gather-development-511211/gather-pilot-images/inference@sha256:b1e299dee4ca949a8b8c10424fffad3c6850f482444addfa15b76f185ecff5e4'


def main():
    wheels=list((ROOT/'output/library-image/wheels').glob('psycopg2_binary-2.9.11-cp312-cp312-manylinux2014_x86_64*.whl'))
    if len(wheels)!=1: raise ValueError('expected_database_wheel_missing')
    wheel=wheels[0]
    with urlopen('https://pypi.org/pypi/psycopg2-binary/2.9.11/json',timeout=15) as response:
        raw=response.read(1024*1024+1)
    if len(raw)>1024*1024: raise ValueError('metadata_too_large')
    metadata=json.loads(raw)
    expected=next(row['digests']['sha256'] for row in metadata['urls'] if row['filename']==wheel.name)
    digest=hashlib.sha256(wheel.read_bytes()).hexdigest()
    if digest!=expected: raise ValueError('database_wheel_hash_mismatch')
    fix=ROOT/'output/library-image/wheels/filelock-4.2.1-py3-none-any.whl'
    with urlopen('https://pypi.org/pypi/filelock/4.2.1/json',timeout=15) as response:
        fix_metadata=json.loads(response.read(1024*1024))
    fix_digest=hashlib.sha256(fix.read_bytes()).hexdigest()
    if fix_digest!=next(row['digests']['sha256'] for row in fix_metadata['urls'] if row['filename']==fix.name):
        raise ValueError('filelock_wheel_hash_mismatch')
    pinned_token_counter(ROOT/'output/inference-model')  # Tokenizer only; validates pinned bytes.
    target=ROOT/'output/library-image'/('context-'+uuid4().hex)
    target.mkdir(parents=True)
    for directory in ('services','scripts'):
        for source in (ROOT/directory).rglob('*.py'):
            if source.is_symlink() or '__pycache__' in source.parts: continue
            dest=target/source.relative_to(ROOT)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,dest)
    (target/'services/inference').mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/'services/inference/model-manifest.json',target/'services/inference/model-manifest.json')
    for directory,source,name in (
        ('tokenizer',ROOT/'output/inference-model/tokenizer.json','tokenizer.json'),
        ('config',ROOT/'output/supabase-cli/prod-ca-2021.crt','supabase-ca.crt'),
        ('wheels',wheel,wheel.name)):
        (target/directory).mkdir()
        shutil.copyfile(source,target/directory/name)
    shutil.copyfile(fix,target/'wheels'/fix.name)
    installer='''import hashlib,json,pathlib,stat,sysconfig,zipfile,shutil
manifest=json.loads(pathlib.Path('/app/database-wheel.json').read_text())
purelib=pathlib.Path(sysconfig.get_path('purelib')).resolve()
for entry in ('filelock','filelock-4.1.1.dist-info'):
    old=purelib/entry
    assert old.resolve().parent==purelib
    if old.exists(): shutil.rmtree(old)
for artifact in manifest['wheels']:
    wheel=pathlib.Path('/wheels')/artifact['file']
    assert hashlib.sha256(wheel.read_bytes()).hexdigest()==artifact['sha256']
    with zipfile.ZipFile(wheel) as archive:
        for member in archive.infolist():
            path=pathlib.PurePosixPath(member.filename)
            assert not path.is_absolute() and '..' not in path.parts and not stat.S_ISLNK(member.external_attr>>16)
            assert path.parts[0] in ('psycopg2','psycopg2_binary.libs','psycopg2_binary-2.9.11.dist-info','filelock','filelock-4.2.1.dist-info')
        archive.extractall(purelib)
import psycopg2
assert psycopg2.__version__.startswith('2.9.11')
import filelock
assert filelock.__version__=='4.2.1'
'''
    (target/'install_database_wheel.py').write_text(installer,encoding='utf-8')
    (target/'database-wheel.json').write_text(json.dumps({'wheels':[{'file':wheel.name,'sha256':digest},{'file':fix.name,'sha256':fix_digest}],'source':'https://pypi.org/'}),encoding='utf-8')
    docker=f'''ARG GATHER_BASE={BASE}
FROM ${{GATHER_BASE}}
USER 0:0
COPY database-wheel.json install_database_wheel.py /app/
RUN --mount=type=bind,source=wheels,target=/wheels python /app/install_database_wheel.py
COPY services /app/services
COPY scripts /app/scripts
COPY config /app/config
COPY tokenizer /app/tokenizer
USER 65532:65532
ENTRYPOINT ["python", "-m", "services.worker.cloud_library"]
'''
    (target/'Dockerfile').write_text(docker,encoding='utf-8')
    (target/'.dockerignore').write_text('**\n!Dockerfile\n!services/\n!services/**\n!scripts/\n!scripts/**\n!config/\n!config/**\n!tokenizer/\n!tokenizer/**\n!wheels/\n!wheels/**\n!database-wheel.json\n!install_database_wheel.py\n',encoding='utf-8')
    receipt={'context':str(target),'base':BASE,'database_wheel_sha256':digest,'includes_credentials':False,'includes_user_documents':False}
    (ROOT/'output/library-image/staging.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt))


if __name__=='__main__': main()
