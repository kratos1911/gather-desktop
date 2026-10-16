"""Coordinator + PostgreSQL integration, using explicitly synthetic vectors only."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'tests/worker'))
from test_ingestion import SyntheticProvider
from services.worker.ingestion import submit, run_once
from services.worker.ingestion_repository import RepositoryError, FUNCTIONS
from services.inference.runtime import InferenceError


def coordinator_checks(name, run):
    def sql(statement):
        return run('exec','-i',name,'psql','-X','-qAt','-U','postgres','-v','ON_ERROR_STOP=1',
                   '-v','VERBOSITY=verbose',input=statement,timeout=10).stdout.strip()

    def literal(value):
        if value is None:
            return 'null'
        if type(value) is bytes:
            return "decode('" + value.hex() + "','hex')"
        if type(value) is int:
            return str(value)
        if isinstance(value,(dict,list)):
            value = json.dumps(value,allow_nan=False)
        return "'" + str(value).replace("'","''") + "'"

    class Database:
        """Test-only psql transport; production DB-API adapter tested separately."""
        def __init__(self, role, owner=None):
            self.role,self.owner = role,owner

        def call(self, function, *args):
            assert function in FUNCTIONS and len(args) == FUNCTIONS[function]
            context = f"set role {self.role};"
            if self.owner:
                context += f"set request.jwt.claim.sub='{self.owner}';"
            try:
                output = sql(context + "set statement_timeout='5s'; set lock_timeout='3s'; "
                    f"select to_jsonb(gather_private.{function}({','.join(map(literal,args))}))")
                return json.loads(output) if output else None
            except subprocess.CalledProcessError as error:
                code = re.search(r'ERROR:\s+(\w{5}):',error.stderr)
                state = code.group(1) if code else ''
                raise RepositoryError('stale_lease' if state == '55000' else
                    ('invalid_input' if state[:2] in ('22','23','42') else 'temporarily_unavailable')) from None

    owner,other = str(uuid.uuid4()),str(uuid.uuid4())
    sql(f"insert into auth.users values('{owner}'),('{other}'); "
        f"insert into gather_private.source_quotas values('{owner}',16,0),('{other}',16,0)")
    admission,worker = Database('gather_ingestion_coordinator',owner),Database('gather_ingestion_worker')
    total = 0

    def check(value,label):
        nonlocal total
        assert value,label
        total += 1
        print('PASS: coordinator ' + label)

    def add(raw=b'Synthetic text '*50, key=None, source=None, media='text/plain', repository=admission):
        return submit(repository,request_id=key or str(uuid.uuid4()),title='Synthetic ingestion',
                      original=raw,media=media,source_id=source)

    def status(item):
        return json.loads(sql(f"select to_jsonb(j) from gather_private.ingestion_jobs j where id='{item['job_id']}'"))

    def visible(item,who=owner):
        return sql(f"set role authenticated; set request.jwt.claim.sub='{who}'; "
                   f"select count(*) from public.read_published_text('{item['source_id']}')")

    def expire(item):
        sql(f"update gather_private.ingestion_jobs set lease_started_at=clock_timestamp()-interval '2 minutes',"
            f"lease_expires_at=clock_timestamp()-interval '1 second' where id='{item['job_id']}'")

    def delete(item):
        sql(f"set role authenticated; set request.jwt.claim.sub='{owner}'; "
            f"select public.request_source_deletion('{item['source_id']}')")

    key = str(uuid.uuid4())
    with ThreadPoolExecutor(max_workers=2) as pool:
        first,duplicate = list(pool.map(lambda _: add(key=key), range(2)))
    check(first == duplicate,'concurrent duplicate submission returns same source/job/version')
    check(sql(f"select used from gather_private.source_quotas where owner_id='{owner}'") == '1','duplicate consumes one quota slot')
    try:
        add(b'changed',key=key)
        raise AssertionError('conflicting replay accepted')
    except RepositoryError:
        check(True,'changed bytes with same request rejected')
    check(run_once(worker,SyntheticProvider())['state'] == 'ready','submission reaches ready without manual processing steps')
    check(status(first)['state'] == 'ready' and int(visible(first)) > 1,'complete multi-passage publication visible')
    check(visible(first,other) == '0','published content isolated by owner')
    for function in ('read_job_original','completed_passages'):
        try:
            Database('authenticated',other).call(function,first['job_id'],str(uuid.uuid4()))
            raise AssertionError('private derivative read allowed')
        except RepositoryError:
            check(True,'client cannot invoke ' + function)
    for role in ('authenticated','anon','gather_ingestion_worker'):
        try:
            add(repository=Database(role,owner))
            raise AssertionError('client admission allowed')
        except RepositoryError:
            check(True,'admission restricted for ' + role)
    try:
        add(repository=Database('gather_ingestion_coordinator',other),source=first['source_id'])
        raise AssertionError('wrong owner replacement allowed')
    except RepositoryError:
        check(True,'replacement enforces trusted context owner')
    try:
        add(repository=Database('gather_ingestion_coordinator'))
        raise AssertionError('missing identity allowed')
    except RepositoryError:
        check(True,'missing trusted identity denied')

    # Crash after one vector commits. A new coordinator must skip that vector.
    interrupted = add(b'# Markdown\r\nCafe\xcc\x81 \xf0\x9f\x8c\x9f\r\n'*35,media='text/markdown')
    class Crash(SyntheticProvider):
        calls = 0
        def infer(self,*args,**kwargs):
            self.calls += 1
            if self.calls == 2:
                raise KeyboardInterrupt()
            return super().infer(*args,**kwargs)
    try:
        run_once(worker,Crash())
    except KeyboardInterrupt:
        pass
    check(status(interrupted)['state'] == 'processing' and visible(interrupted) == '0','interruption leaves durable hidden work')
    check(sql(f"select count(*) from gather_private.staged_passages where version_id='{interrupted['version_id']}' and embedding is not null") == '1',
          'interruption preserves one completed vector')
    expire(interrupted)
    class Counting(SyntheticProvider):
        calls = 0
        def infer(self,*args,**kwargs):
            self.calls += 1
            return super().infer(*args,**kwargs)
    resumed = Counting()
    check(run_once(Database('gather_ingestion_worker'),resumed)['state'] == 'ready'
          and status(interrupted)['attempts'] == 2,'fresh coordinator recovers original and staged passages')
    check(resumed.calls == int(visible(interrupted))-1,'recovery embeds only missing passages')

    retry = add()
    class Timeout(SyntheticProvider):
        def infer(self,*args,**kwargs):
            raise InferenceError('deadline_exceeded')
    check(run_once(worker,Timeout())['error_code'] == 'timeout' and status(retry)['state'] == 'queued','timeout visibly queued with durable retry')
    check(run_once(worker,SyntheticProvider())['state'] == 'idle','retry backoff respected')
    sql(f"update gather_private.ingestion_jobs set next_attempt_at=clock_timestamp()-interval '1 second' where id='{retry['job_id']}'")
    check(run_once(worker,SyntheticProvider())['state'] == 'ready','retry completes after backoff')

    invalid = add()
    class Invalid(SyntheticProvider):
        def infer(self,request,*,cancel):
            result = super().infer(request,cancel=cancel)
            result['data'][0]['embedding'][0] = float('nan')
            return result
    check(run_once(worker,Invalid())['state'] == 'failed' and visible(invalid) == '0','invalid vector output terminal and unpublished')

    replacing = add(source=first['source_id'])
    newer = []
    class Replace(SyntheticProvider):
        def infer(self,request,*,cancel):
            newer.append(add(b'new replacement',source=first['source_id']))
            return super().infer(request,cancel=cancel)
    check(run_once(worker,Replace())['state'] == 'abandoned' and int(visible(first)) > 0,'supersession stops stale worker and retains prior publication')
    check(run_once(worker,SyntheticProvider())['state'] == 'ready','replacement completes through same coordinator')

    deleting = add()
    class DeleteDuringRequest(SyntheticProvider):
        def infer(self,request,*,cancel):
            delete(deleting)
            # Real ten-second heartbeat must detect deletion while request is active.
            if not cancel.wait(13):
                raise AssertionError('heartbeat did not cancel active provider')
            raise InferenceError('cancelled')
    check(run_once(worker,DeleteDuringRequest())['state'] == 'abandoned','heartbeat cancels an active request after deletion')
    check(visible(deleting) == '0' and status(deleting)['state'] == 'cancelled','late result cannot restore deleted source')
    try:
        add(source=deleting['source_id'])
        raise AssertionError('deleted source resurrected')
    except RepositoryError:
        check(True,'deleted source rejects new submission')

    sources = json.loads(sql(f"select jsonb_agg(id) from public.sources where owner_id='{owner}'"))
    for source in sources:
        delete({'source_id':source})
        sql(f"select gather_private.finish_source_cleanup('{source}')")
    check(sql('select count(*) from gather_private.job_originals') == '0','cleanup removes all durable handoff originals')
    print(f'Coordinator integration checks passed: {total}. Synthetic provider, no live inference or JWT evidence.')
