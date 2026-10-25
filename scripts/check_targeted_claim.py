"""Real PostgreSQL exact-claim checks; disposable fixtures only, no models."""
from concurrent.futures import ThreadPoolExecutor
import json
import subprocess
import uuid


def targeted_claim_checks(name, run):
    def sql(statement):
        return run('exec','-i',name,'psql','-X','-qAt','-U','postgres',
                   '-v','ON_ERROR_STOP=1',input=statement,timeout=10).stdout.strip()
    owner = str(uuid.uuid4())
    sql(f"insert into auth.users values('{owner}'); insert into gather_private.source_quotas values('{owner}',4,0)")
    sources = []
    def add(source=None):
        if source is None:
            source = sql(f"set role authenticated; set request.jwt.claim.sub='{owner}'; "
                "select public.save_source(gen_random_uuid(),'file','Synthetic exact-claim fixture')")
            sources.append(source)
        job = sql(f"select gather_private.enqueue_text_job('{owner}','{source}',gen_random_uuid(),"
            "repeat('a',64),'fixture-v1',32,'text/plain','fixture-chunks','fixture-model','fixture-revision',512)")
        return source,job
    def claim(job=None):
        function = 'claim_text_job()' if job is None else f"claim_target_text_job('{job}')"
        result = sql('set role gather_ingestion_worker; select coalesce(gather_private.'+function+"::text,'null')")
        return json.loads(result)
    def expire(job):
        sql(f"update gather_private.ingestion_jobs set lease_started_at=clock_timestamp()-interval '2 minutes',"
            f"lease_expires_at=clock_timestamp()-interval '1 second' where id='{job}'")
    def status(job):
        return json.loads(sql(f"select to_jsonb(j) from gather_private.ingestion_jobs j where id='{job}'"))
    def check(condition,label):
        assert condition,label
        print('PASS: exact claim '+label)
    _,old = add()
    source,target = add()
    first_old = claim()
    check(first_old['id']==old,'legacy FIFO still selects oldest')
    expire(old)
    first = claim(target)
    check(first['id']==target and first['attempts']==1,'requested job bypasses unrelated expired job')
    check(status(old)['attempts']==1 and status(old)['state']=='processing','unrelated job and retry budget unchanged')
    check(claim(old) is None and claim() is None,'targeted and general callers share global live lease limit')
    for role in ('anon','authenticated','gather_ingestion_coordinator','gather_ingestion_worker'):
        expected = 't' if role=='gather_ingestion_worker' else 'f'
        check(sql(f"select has_function_privilege('{role}','gather_private.claim_target_text_job(uuid)','EXECUTE')")==expected,
              role+' exact-claim permission')
        check(sql(f"select has_function_privilege('{role}','gather_private.claim_text_job_internal(uuid)','EXECUTE')")=='f',
              role+' cannot invoke shared private core')
    expire(target)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _:claim(target),range(2)))
    live = [r for r in results if r is not None]
    check(len(live)==1 and live[0]['attempts']==2,'concurrent exact claim grants one fresh lease')
    check(live[0]['lease_token']!=first['lease_token'],'recovery changes fencing token')
    try:
        sql(f"set role gather_ingestion_worker; select gather_private.renew_text_job('{target}','{first['lease_token']}')")
        raise AssertionError('stale token renewed')
    except subprocess.CalledProcessError as error:
        check('stale_lease' in error.stderr,'old token stays fenced')
    sql(f"set role gather_ingestion_worker; select gather_private.fail_text_job('{target}','{live[0]['lease_token']}','timeout')")
    check(claim(target) is None and status(old)['attempts']==1,'target backoff does not fall through to another job')
    sql(f"update gather_private.ingestion_jobs set next_attempt_at=clock_timestamp()-interval '1 second' where id='{target}'")
    check(claim(target)['attempts']==3,'existing final retry remains available')
    expire(target)
    check(claim(target) is None and status(target)['state']=='failed' and status(target)['attempts']==3,
          'exhausted target retired without fourth attempt')
    check(claim(str(uuid.uuid4())) is None,'missing target does not fall through')
    check(sql('set role gather_ingestion_worker; select gather_private.claim_target_text_job(null) is null')=='t','null target cannot claim FIFO')
    resumed = claim()
    check(resumed['id']==old and resumed['attempts']==2,'general dispatcher still recovers older work')
    sql(f"set role gather_ingestion_worker; select gather_private.fail_text_job('{old}','{resumed['lease_token']}','invalid_input')")
    _,replaced = add(source)
    _,newer = add(source)
    check(claim(replaced) is None,'superseded target cannot be claimed')
    check(claim(newer)['id']==newer,'current replacement can be claimed')
    for sid in sources:
        sql(f"set role authenticated; set request.jwt.claim.sub='{owner}'; select public.request_source_deletion('{sid}')")
        sql(f"select gather_private.finish_source_cleanup('{sid}')")
    check(claim(newer) is None,'deleted target cannot be restored')
