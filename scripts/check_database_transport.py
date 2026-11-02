"""Actual psycopg transport, limited logins and disposable SQL. No hosted access."""
import json
import secrets
import subprocess
import time
import uuid
import argparse
from dataclasses import asdict,replace
import base64
import re

from scripts.check_database import ROOT, IMAGE, run
from services.worker.database_transport import DatabaseConfig, DatabaseRepository
from services.worker.ingestion import submit, run_once
from services.worker.ingestion_repository import RepositoryError
from tests.worker.test_ingestion import SyntheticProvider


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--performance',action='store_true',help='Also verify scoped worker reuse/context reset and record local fixture timings.')
    parser.add_argument('--runtime-image',help='Additionally verify this exact Linux API image at 512 MiB/1 CPU.')
    args_cli=parser.parse_args()
    if args_cli.runtime_image and (not args_cli.performance or not re.fullmatch(r'sha256:[0-9a-f]{64}',args_cli.runtime_image)):
        parser.error('runtime-image requires performance and an exact local image digest.')
    run('info','--format','{{.ServerVersion}}',timeout=15)
    run('image','inspect',IMAGE,timeout=10)
    name = 'gather-driver-check-'+uuid.uuid4().hex
    created = False
    try:
        run('run','--detach','--name',name,'--memory','256m','--cpus','1','--pids-limit','100',
            '--publish','127.0.0.1::5432','--tmpfs','/var/lib/postgresql/data:rw,size=192m,uid=100,gid=101',
            '--user','100:101','--env','PGHOST=/tmp','--mount',
            f'type=bind,source={ROOT / "tests/database/start-driver-postgres.sh"},target=/gather-start.sh,readonly',
            '--entrypoint','sh',IMAGE,'/gather-start.sh')
        created = True
        ports = json.loads(run('inspect','--format','{{json .NetworkSettings.Ports}}',name).stdout)
        bindings = ports['5432/tcp']
        assert len(bindings)==1 and bindings[0]['HostIp']=='127.0.0.1'
        port = int(bindings[0]['HostPort'])
        for _ in range(30):
            try:
                run('exec',name,'pg_isready','-U','postgres',timeout=5)
                break
            except subprocess.CalledProcessError:
                time.sleep(.5)
        else:
            raise RuntimeError('test_database_unavailable')
        def sql(statement):
            return run('exec','-i',name,'psql','-X','-qAt','-U','postgres','-v','ON_ERROR_STOP=1',
                       input=statement,timeout=10).stdout.strip()
        sql('\n'.join(p.read_text(encoding='utf-8') for p in
            [ROOT/'tests/database/bootstrap.sql',*sorted((ROOT/'supabase/migrations').glob('*.sql'))]))
        passwords = {role:secrets.token_urlsafe(32) for role in ('gather_admission','gather_worker')}
        for login,role in (('gather_admission','gather_ingestion_coordinator'),('gather_worker','gather_ingestion_worker')):
            sql(f"create role {login} login noinherit password '{passwords[login]}'; grant {role} to {login}")
        configs = {role:DatabaseConfig('127.0.0.1',port,role,passwords[role],test_loopback=True) for role in passwords}
        owner,other = str(uuid.uuid4()),str(uuid.uuid4())
        sql(f"insert into auth.users values('{owner}'),('{other}'); insert into gather_private.source_quotas values('{owner}',2,0),('{other}',2,0)")
        first = DatabaseRepository(configs['gather_admission'],owner=owner)
        second = DatabaseRepository(configs['gather_admission'],owner=other)
        worker = DatabaseRepository(configs['gather_worker'])
        key = str(uuid.uuid4())
        args = dict(request_id=key,title='Driver fixture',original=b'Synthetic database transport text.',media='text/plain')
        item = submit(first,**args)
        assert submit(first,**args)==item
        assert sql(f"select owner_id from public.sources where id='{item['source_id']}'")==owner
        print('PASS: real driver admission binds owner and preserves duplicate identity')
        try:
            submit(second,**(args | {'request_id':str(uuid.uuid4()),'source_id':item['source_id']}))
            raise AssertionError('foreign replacement accepted')
        except RepositoryError:
            pass
        other_item = submit(second,**(args | {'request_id':str(uuid.uuid4())}))
        assert sql(f"select owner_id from public.sources where id='{other_item['source_id']}'")==other
        print('PASS: fresh transactions isolate owners and reject foreign replacement')
        for _ in range(2):
            result = run_once(worker,SyntheticProvider())
            if result['state']!='ready':
                print('Safe job outcome:',{k:result[k] for k in ('state','error_code') if k in result})
                raise AssertionError('driver processing failed')
        assert worker.call('claim_text_job') is None
        print('PASS: actual driver processes originals, stages vectors and publishes both jobs')
        # Deliberate function error: rollback must not leave a partial original/version.
        before = sql('select count(*) from public.source_versions')
        try:
            submit(first,**(args | {'original':b'conflicting bytes'}))
            raise AssertionError('conflicting retry accepted')
        except RepositoryError:
            pass
        assert sql('select count(*) from public.source_versions')==before
        print('PASS: conflicting retry rolls back without additional versions')
        if args_cli.performance:
            performance_checks(configs,first,args,item,sql)
        if args_cli.runtime_image:
            fixture_owner=str(uuid.uuid4())
            sql(f"insert into auth.users values('{fixture_owner}'); insert into gather_private.source_quotas values('{fixture_owner}',1,0)")
            payload={'owner':fixture_owner,'configs':{key:asdict(replace(value,port=5432)) for key,value in configs.items()},
                     'pdf':base64.b64encode((ROOT/'output/pdf-pilot/hosted-pilot.pdf').read_bytes()).decode()}
            result=run('run','--rm','-i','--network','container:'+name,'--memory','512m','--cpus','1',
                '--pids-limit','64','--read-only','--tmpfs','/tmp:rw,size=16m',
                '--entrypoint','python',args_cli.runtime_image,'-B','-m','scripts.check_worker_runtime',
                input=json.dumps(payload),timeout=45)
            measurements=json.loads(result.stdout)
            assert measurements.get('passed') is True,'runtime composition failed'
            (ROOT/'output/processing-speed/linux-runtime.json').write_text(json.dumps(measurements,indent=2))
            print('PASS: exact Linux image, PDF/tokenizer and two real DB helpers fit 512 MiB/1 CPU; no model calls')
        sql('alter role gather_worker bypassrls')
        try:
            worker.call('claim_text_job')
            raise AssertionError('privileged login accepted')
        except RepositoryError:
            pass
        print('PASS: runtime rejects privileged database login')
        print('Driver integration passed: real limited logins/transactions, synthetic vectors, local TLS bypass only.')
    finally:
        if created:
            run('rm','-f','-v',name)
            print('Disposable driver database removed.')


def performance_checks(configs,admission,args,item,sql):
    """Actual DB sessions, synthetic data. This is not hosted latency evidence."""
    from services.worker.worker_lifecycle import WorkerRun
    import threading
    workers={name:DatabaseRepository(configs['gather_worker'],reuse_worker=reuse)
             for name,reuse in (('baseline',False),('reuse',True))}
    samples={}
    for name,worker in workers.items():
        submit(admission,**(args|{'request_id':str(uuid.uuid4()),'source_id':item['source_id']}))
        result=WorkerRun(worker,SyntheticProvider(),record_timings=True).run()['outcomes'][0]
        assert result['state']=='ready','profiled fixture did not publish'
        samples[name]=result['timing']
    assert samples['baseline']['database']['connects']>samples['reuse']['database']['connects'], 'connections were not reused'
    assert samples['reuse']['database']['connects']<=2,'more than two job helper sessions'
    print('PASS: same synthetic source publishes with fewer actual worker connections')
    original_next=sql("select pg_get_functiondef('gather_private.next_automatic_text_job()'::regprocedure)")
    original_claim=sql("select pg_get_functiondef('gather_private.claim_text_job()'::regprocedure)")
    try:
        sql("""create or replace function gather_private.next_automatic_text_job() returns uuid
            language plpgsql security invoker set search_path='' as $$
            begin perform pg_catalog.set_config('request.jwt.claim.sub','synthetic-poison',false); return null;end $$;
            create or replace function gather_private.claim_text_job() returns jsonb
            language sql security invoker set search_path='' as $$
            select jsonb_build_object('role',current_user,'owner',current_setting('request.jwt.claim.sub',true),
             'pid',pg_backend_pid(),'statement_timeout',current_setting('statement_timeout')) $$;""")
        reused=workers['reuse']
        with reused.job_scope():
            first=reused.call('claim_text_job')
            reused.call('next_automatic_text_job')  # Deliberately contaminates this test session.
            second=reused.call('claim_text_job')
            assert first['pid']==second['pid'],'worker did not retain its connection'
            assert second['owner']=='' and second['role']=='gather_ingestion_worker','session context leaked'
            assert second['statement_timeout']=='5s','statement timeout changed'
            print('PASS: reused backend PID resets owner context, role and SQL deadline each transaction')
            heartbeat=[]
            thread=threading.Thread(target=lambda:heartbeat.append(reused.call('claim_text_job')))
            thread.start();thread.join(6)
            assert not thread.is_alive() and len(heartbeat)==1,'heartbeat test did not complete'
            assert heartbeat[0]['pid']!=second['pid'],'heartbeat shared the active operation connection'
            assert submit(admission,**args)==item,'fresh admission identity changed under cache pressure'
            print('PASS: independent heartbeat session and fresh admission survive idle-helper eviction')
    finally:
        sql(original_next+';\n'+original_claim)
    with workers['reuse'].job_scope():
        workers['reuse'].call('next_automatic_text_job')
        try:
            workers['reuse'].call('renew_text_job',str(uuid.uuid4()),str(uuid.uuid4()))
            raise AssertionError('stale lease accepted')
        except RepositoryError as error:
            assert error.code=='stale_lease','SQL failure mapping changed'
        assert workers['reuse'].call('next_automatic_text_job') is None,'independent operation did not recover cleanly'
    assert workers['reuse'].last_job_metrics['helpers_started']==2,'failed connection was reused'
    print('PASS: SQL failure rolls back, discards the helper and never replays the failed operation')
    replacement=submit(admission,**(args|{'request_id':str(uuid.uuid4()),'source_id':item['source_id']}))
    class DeleteDuringInference(SyntheticProvider):
        def infer(self,request,*,cancel):
            sql("set request.jwt.claim.sub='"+sql("select owner_id from public.sources where id='"+item['source_id']+"'")+"';"+
                "select public.request_source_deletion('"+item['source_id']+"')")
            return super().infer(request,cancel=cancel)
    outcome=WorkerRun(workers['reuse'],DeleteDuringInference(),record_timings=True).run()['outcomes'][0]
    assert outcome['state']=='abandoned','cached transaction ignored deletion'
    assert sql("select count(*) from gather_private.staged_passages where version_id='"+replacement['version_id']+"' and embedding is not null")=='0'
    print('PASS: deletion between reused transactions fences vector storage and publication')
    with workers['reuse'].job_scope():
        workers['reuse'].call('next_automatic_text_job')
        sql('alter role gather_worker bypassrls')
        try:
            try:
                workers['reuse'].call('next_automatic_text_job')
                raise AssertionError('privilege escalation survived cached connection')
            except RepositoryError:pass
        finally:sql('alter role gather_worker nobypassrls')
    print('PASS: cached connection rechecks restricted login privileges')
    destination=ROOT/'output/processing-speed'
    destination.mkdir(parents=True,exist_ok=True)
    (destination/'local-comparison.json').write_text(json.dumps({
        'scope':'Local disposable PostgreSQL and synthetic vectors; no hosted/model speedup claim',
        'samples':samples,'same_source_bytes':True,'hosted':False},indent=2))
    print('Local timing receipt: output/processing-speed/local-comparison.json')


if __name__=='__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Driver check failed; credentials and database details withheld.') from None
