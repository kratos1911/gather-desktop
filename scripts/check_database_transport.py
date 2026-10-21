"""Actual psycopg transport, limited logins and disposable SQL. No hosted access."""
import json
import secrets
import subprocess
import time
import uuid

from scripts.check_database import ROOT, IMAGE, run
from services.worker.database_transport import DatabaseConfig, DatabaseRepository
from services.worker.ingestion import submit, run_once
from services.worker.ingestion_repository import RepositoryError
from tests.worker.test_ingestion import SyntheticProvider


def main():
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


if __name__=='__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Driver check failed; credentials and database details withheld.') from None
