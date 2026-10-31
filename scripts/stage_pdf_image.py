"""Stage a small PDF-capable overlay on the exact verified library image."""
import hashlib
import argparse
import json
from pathlib import Path
import shutil
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
BASE='sha256:522826fd030d34807e17c2073c1b23d8376a30d215d936f738e74f83a4cc3724'
HASH='33e4fb41ca352810eb4e9838aa0d82d6888a5f8bf682f43e99cce5faa666255c'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recovery',action='store_true',help='Stage recovery fixes over the deployed PDF image; preserve PDF evidence.')
    recovery=parser.parse_args().recovery
    wheel=ROOT/'output/pdf-pilot/wheels/pypdf-6.21.4-py3-none-any.whl'
    if hashlib.sha256(wheel.read_bytes()).hexdigest()!=HASH:raise ValueError('parser_hash_mismatch')
    artifact_directory=ROOT/('output/recovery-fix' if recovery else 'output/pdf-pilot')
    artifact_directory.mkdir(parents=True,exist_ok=True)
    target=artifact_directory/('context-'+uuid4().hex);target.mkdir()
    for directory in ('services','scripts'):
        for source in (ROOT/directory).rglob('*.py'):
            if source.is_symlink() or '__pycache__' in source.parts:continue
            dest=target/source.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
    shutil.copyfile(wheel,target/wheel.name)
    install="""import hashlib,pathlib,stat,sysconfig,zipfile
p=pathlib.Path('/app/pypdf-6.21.4-py3-none-any.whl')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='"""+HASH+"""'
with zipfile.ZipFile(p) as z:
 for m in z.infolist():
  a=pathlib.PurePosixPath(m.filename)
  assert not a.is_absolute() and '..' not in a.parts and not stat.S_ISLNK(m.external_attr>>16)
  assert a.parts[0] in ('pypdf','pypdf-6.21.4.dist-info')
 z.extractall(sysconfig.get_path('purelib'))
import pypdf
assert pypdf.__version__=='6.21.4'
p.unlink()
"""
    (target/'install_pdf.py').write_text(install)
    base='sha256:72ce93fda395473d17dbce81247ced97f138e334ff8fef3c949cfb2ec479db8d' if recovery else BASE
    base_ref='asia-south1-docker.pkg.dev/gather-development-511211/gather-pilot-images/library@'+base
    (target/'Dockerfile').write_text('FROM '+base_ref+'''
USER 0:0
COPY pypdf-6.21.4-py3-none-any.whl install_pdf.py /app/
RUN python /app/install_pdf.py
COPY services /app/services
COPY scripts /app/scripts
USER 65532:65532
ENTRYPOINT ["python","-m","services.worker.cloud_library"]
''')
    (target/'.dockerignore').write_text('**\n!Dockerfile\n!install_pdf.py\n!*.whl\n!services/\n!services/**\n!scripts/\n!scripts/**\n')
    receipt={'context':str(target),'base':base,'parser_sha256':HASH,'credentials_included':False,'user_documents_included':False}
    (artifact_directory/'staging.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt))


if __name__=='__main__':main()
