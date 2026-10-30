"""Explicit managed-cloud composition. No local secret or caller-token fallback."""
import os
from pathlib import Path
from scripts.operator_library import compose_pilot
from scripts.check_cloud_ingestion import BoundedProvider,IDENTITY
from services.worker.cloud_identity import MetadataTokenProvider
from services.worker.cloud_provider import cloud_provider
from services.worker.database_transport import DatabaseConfig
from services.worker.library_server import create_cloud_server

PROJECT='gather-development-511211'
SUPABASE='fatolholcjxpwocnpzws'


def configuration(environment):
    if environment.get('K_SERVICE')!='gather-library-pilot' or environment.get('PORT')!='8080' or environment.get('GATHER_PROJECT')!=PROJECT:
        raise ValueError('invalid_cloud_library_target')
    key=environment.get('GATHER_PUBLISHABLE_KEY','')
    if not key.startswith('sb_publishable_') or len(key)>8192 or any(c.isspace() for c in key):
        raise ValueError('invalid_public_configuration')
    configs=[]
    for role in ('gather_admission','gather_worker'):
        path=Path('/secrets')/role/'password'
        if path.is_symlink() or not path.is_file() or path.stat().st_size>4096:
            raise ValueError('cloud_secret_unavailable')
        # Preserve exact password bytes; secret material is never logged.
        password=path.read_text(encoding='utf-8')
        configs.append(DatabaseConfig('aws-0-ap-southeast-2.pooler.supabase.com',5432,
            role+'.'+SUPABASE,password,root_certificate='/app/config/supabase-ca.crt',connect_timeout=10))
    return key,configs


def main():
    key,(admission,worker)=configuration(os.environ)
    identity=MetadataTokenProvider(IDENTITY)
    try:
        identity.get()  # Prime metadata identity before accepting user requests.
        provider=BoundedProvider(cloud_provider(IDENTITY,Path('/app/tokenizer'),token_provider=identity))
        def record(_job,result):
            print('Automatic processing: '+','.join(r['state'] for r in result['outcomes']),flush=True)
        app=compose_pilot(admission,worker,provider,identity,key,text_files=True,automatic=True,record=record)
        create_cloud_server(app,os.environ).run()
    finally: identity.invalidate()


if __name__=='__main__':
    try: main()
    except Exception: raise SystemExit('cloud_library_unavailable') from None
