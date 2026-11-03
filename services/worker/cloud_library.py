"""Explicit managed-cloud composition. No local secret or caller-token fallback."""
import os
import json
from pathlib import Path
from scripts.operator_library import compose_pilot
from scripts.check_cloud_ingestion import BoundedProvider,IDENTITY
from services.worker.cloud_identity import MetadataTokenProvider
from services.worker.cloud_provider import cloud_provider
from services.worker.database_transport import DatabaseConfig
from services.worker.library_server import create_cloud_server

PROJECT='gather-development-511211'
SUPABASE='fatolholcjxpwocnpzws'


def processing_log(result,calls):
    """Allowlisted diagnostics only. Never serialize a worker result verbatim."""
    states={'ready','queued','processing','failed','cancelled','unavailable','idle','stopped'}
    value={'states':[row['state'] for row in result.get('outcomes',[])
        if type(row) is dict and row.get('state') in states]}
    startup=result.get('startup_error')
    if startup in {'cloud_identity_unavailable','cloud_startup_deadline_exceeded','cloud_startup_probe_failed',
        'cloud_startup_http_401','cloud_startup_http_403','cloud_startup_http_429','cloud_startup_http_503',
        'cloud_startup_network_timeout','cloud_startup_tls_failed','cloud_startup_dns_failed',
        'cloud_startup_connection_failed','cloud_startup_readiness_probe_failed','startup_unavailable'}:
        value['startup_error']=startup
    if type(calls) is int and 0<=calls<=3:value['model_attempts_used']=calls
    from services.worker.processing_timing import safe_timing
    timings=[safe_timing(row.get('timing')) for row in result.get('outcomes',[]) if type(row) is dict]
    timings=[entry for entry in timings if entry is not None]
    if timings:value['timings']=timings
    return 'Automatic processing: '+json.dumps(value,separators=(',',':'))


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
            print(processing_log(result,provider.calls),flush=True)
        app=compose_pilot(admission,worker,provider,identity,key,text_files=True,automatic=True,record=record,
            pdf_files=os.environ.get('GATHER_PDF_PILOT')=='1',
            docx_files=os.environ.get('GATHER_DOCX_PILOT')=='1',
            reuse_worker=os.environ.get('GATHER_WORKER_DB_REUSE')=='1',
            early_prepare=os.environ.get('GATHER_EARLY_MODEL_START')=='1',
            record_timings=os.environ.get('GATHER_PIPELINE_TIMING')=='1')
        create_cloud_server(app,os.environ).run()
    finally: identity.invalidate()


if __name__=='__main__':
    try: main()
    except Exception: raise SystemExit('cloud_library_unavailable') from None
