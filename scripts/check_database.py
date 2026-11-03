"""Disposable PostgreSQL ownership checks. No host ports, volumes or real data."""
from pathlib import Path
import argparse
import subprocess
import time
import uuid
import json
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'public.ecr.aws/supabase/postgres@sha256:06ddc7962e11ab0f4f0334fd05671e97c30ea202f6e6a7113800bd3d6e416108'


def run(*args, input=None, timeout=60):
    return subprocess.run(['docker', *args], input=input, text=True, encoding='utf-8',
                          capture_output=True, check=True, timeout=timeout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--listing-only',action='store_true',help='Apply schema and run only source listing acceptance checks.')
    parser.add_argument('--automatic-only',action='store_true',help='Apply schema and run automatic dispatch and exact-claim checks.')
    parser.add_argument('--cleanup-only',action='store_true',help='Apply schema and verify only owner-scoped cleanup.')
    parser.add_argument('--pdf-only',action='store_true',help='Apply schema and verify only PDF publication/ownership/citations.')
    parser.add_argument('--recovery-only',action='store_true',help='Verify owner-scoped recovery eligibility without models.')
    parser.add_argument('--docx-only',action='store_true',help='Verify DOCX publication/citations plus existing PDF compatibility.')
    args = parser.parse_args()
    # Fail clearly before creating anything if Docker is unavailable.
    run('info', '--format', '{{.ServerVersion}}', timeout=15)
    name = 'gather-db-check-' + uuid.uuid4().hex
    try:
        run('run', '--detach', '--name', name, '--network', 'none',
            '--memory', '256m', '--cpus', '1', '--pids-limit', '100',
            '--tmpfs', '/var/lib/postgresql/data:rw,size=192m,uid=100,gid=101',
            '--user', '100:101', '--env', 'PGHOST=/tmp',
            '--mount', f'type=bind,source={ROOT / "tests/database/start-postgres.sh"},target=/gather-start.sh,readonly',
            '--entrypoint', 'sh', IMAGE, '/gather-start.sh')
        for _ in range(60):
            try:
                run('exec', name, 'pg_isready', '-U', 'postgres', timeout=5)
                break
            except subprocess.CalledProcessError:
                time.sleep(0.5)
        else:
            raise RuntimeError('Disposable database did not become ready')
        files = [ROOT / 'tests/database/bootstrap.sql',
                 *sorted((ROOT / 'supabase/migrations').glob('*.sql')),
                 ROOT / ('tests/database/docx_publication.sql' if args.docx_only else 'tests/database/recovery_readiness.sql' if args.recovery_only else 'tests/database/pdf_publication.sql' if args.pdf_only else 'tests/database/owned_cleanup.sql' if args.cleanup_only else 'tests/database/automatic_processing.sql' if args.automatic_only else 'tests/database/source_listing.sql')]
        files += ([] if args.listing_only or args.automatic_only or args.cleanup_only or args.pdf_only or args.recovery_only or args.docx_only else [
                 ROOT / 'tests/database/ownership.sql',
                 ROOT / 'tests/database/lifecycle.sql',
                 ROOT / 'tests/database/ingestion_jobs.sql'])
        if args.docx_only: files.append(ROOT/'tests/database/pdf_publication.sql')
        result = run('exec', '-i', name, 'psql', '-X', '-U', 'postgres',
                     '-v', 'ON_ERROR_STOP=1', input='\n'.join(
                         path.read_text(encoding='utf-8') for path in files))
        for line in result.stderr.splitlines():
            if 'PASS:' in line:
                print(line)
        if args.docx_only:
            print('DOCX storage and PDF compatibility checks passed. Synthetic identities/bytes/vectors; no parser or hosted semantic claim.')
            return
        if args.recovery_only:
            print('Recovery eligibility SQL checks passed with synthetic identities; no hosted data or model calls.')
            return
        if args.pdf_only:
            print('PDF SQL publication checks passed. Synthetic bytes/identities/vectors, not parser or hosted semantic proof.')
            return
        if args.cleanup_only:
            print('Owned cleanup SQL checks passed with synthetic identities; no hosted data was changed.')
            return
        if args.automatic_only:
            from check_targeted_claim import targeted_claim_checks
            targeted_claim_checks(name, run)
            print('Automatic dispatch and existing exact-claim checks passed. Synthetic Auth shim; not hosted evidence.')
            return
        if args.listing_only:
            print('Listing SQL checks passed. Auth is a test-only claim shim; hosted Auth/PostgREST is unverified.')
            return
        concurrency_checks(name)
        ingestion_concurrency_checks(name)
        from check_targeted_claim import targeted_claim_checks
        targeted_claim_checks(name, run)
        from check_publication import publication_checks
        publication_checks(name, run)
        from check_ingestion import coordinator_checks
        coordinator_checks(name, run)
        print('Database checks passed. Auth/Storage services were not tested.')
    except subprocess.CalledProcessError as error:
        print(error.stderr)
        raise
    finally:
        # Exact random task container only. No global prune or shared services.
        run('rm', '-f', '-v', name)


def concurrency_checks(name):
    """Separate connections exercise contention against the real SQL engine."""
    def sql(statement):
        return run('exec', '-i', name, 'psql', '-X', '-At', '-U', 'postgres',
                   '-v', 'ON_ERROR_STOP=1', input=statement).stdout.strip()

    owner = '00000000-0000-0000-0000-000000000004'
    sql(f"insert into auth.users values('{owner}'); "
        f"insert into gather_private.source_quotas values('{owner}',1,0);")
    def save(key):
        try:
            return sql(f"set role authenticated; set request.jwt.claim.sub='{owner}'; "
                       f"select public.save_source('{key}','file','Race');").splitlines()[-1]
        except subprocess.CalledProcessError as error:
            if 'source_quota_exceeded' in error.stderr:
                return 'quota'
            raise

    key = str(uuid.uuid4())
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(save, [key, key]))
    assert results[0] == results[1] and results[0] != 'quota', results
    source = results[0]
    assert sql(f"select used from gather_private.source_quotas where owner_id='{owner}'") == '1'
    print('PASS: concurrent identical saves consume one slot')
    sql(f"set role authenticated; set request.jwt.claim.sub='{owner}'; "
        f"select public.request_source_deletion('{source}');")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: sql(
            f"select gather_private.finish_source_cleanup('{source}')"), range(2)))
    assert sorted(results) == ['f', 't'], results
    assert sql(f"select used from gather_private.source_quotas where owner_id='{owner}'") == '0'
    print('PASS: concurrent cleanup releases quota once')
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(save, [str(uuid.uuid4()), str(uuid.uuid4())]))
    assert results.count('quota') == 1, results
    assert sql(f"select count(*) from public.sources where owner_id='{owner}'") == '1'
    print('PASS: concurrent distinct saves cannot exceed one-slot quota')
    source = next(item for item in results if item != 'quota')
    def write_version():
        try:
            sql(f"insert into public.source_versions(source_id,owner_id,content_sha256,parser_version) "
                f"values('{source}','{owner}',repeat('e',64),'race')")
            return 'written'
        except subprocess.CalledProcessError as error:
            if 'source_not_writable' in error.stderr:
                return 'blocked'
            raise
    def delete_source():
        return sql(f"set role authenticated; set request.jwt.claim.sub='{owner}'; "
                   f"select public.request_source_deletion('{source}')")
    with ThreadPoolExecutor(max_workers=2) as pool:
        write = pool.submit(write_version)
        deletion = pool.submit(delete_source)
        assert write.result() in ('written', 'blocked')
        assert deletion.result().splitlines()[-1] == 't'
    sql(f"select gather_private.finish_source_cleanup('{source}')")
    assert sql(f"select count(*) from public.source_versions where source_id='{source}'") == '0'
    print('PASS: concurrent version write/delete leaves no derivative after cleanup')


def ingestion_concurrency_checks(name):
    """Committed leases survive worker disconnect; real sessions race lifecycle writes."""
    def sql(statement):
        return run('exec', '-i', name, 'psql', '-X', '-At', '-U', 'postgres',
                   '-v', 'ON_ERROR_STOP=1', input=statement).stdout.strip().splitlines()[-1]

    owner = '00000000-0000-0000-0000-000000000007'
    sql(f"insert into auth.users values('{owner}'); "
        f"insert into gather_private.source_quotas values('{owner}',2,0);")
    source = sql(f"set role authenticated; set request.jwt.claim.sub='{owner}'; "
                 "select public.save_source(gen_random_uuid(),'file','Synthetic race');")

    def enqueue(key):
        return sql(f"select gather_private.enqueue_text_job('{owner}','{source}','{key}',"
                   "repeat('a',64),'fixture-v1',32,'text/plain','fixture-chunks',"
                   "'fixture-model','fixture-revision',512)")

    key = str(uuid.uuid4())
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = list(pool.map(enqueue, [key, key]))
    job = jobs[0]
    assert jobs[0] == jobs[1]
    assert sql(f"select count(*) from public.source_versions where source_id='{source}'") == '1'
    print('PASS: concurrent enqueue creates exactly one job and version')

    def claim(_):
        value = sql("set role gather_ingestion_worker; "
                    "select coalesce(gather_private.claim_text_job()::text,'none')")
        return None if value == 'none' else json.loads(value)

    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(claim, range(2)))
    assert sum(c is not None for c in claims) == 1, claims
    first = next(c for c in claims if c)
    assert first['id'] == job and first['attempts'] == 1
    assert claim(0) is None  # Earlier claiming psql connection has already exited.
    print('PASS: concurrent claim is exclusive and survives worker disconnect')

    sql(f"update gather_private.ingestion_jobs set lease_started_at=clock_timestamp()-interval '2 minutes',"
        f"lease_expires_at=clock_timestamp()-interval '1 second' where id='{job}'")
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(claim, range(2)))
    assert sum(c is not None for c in claims) == 1, claims
    recovered = next(c for c in claims if c)
    assert recovered['attempts'] == 2 and recovered['lease_token'] != first['lease_token']
    print('PASS: concurrent recovery grants one fresh token and increments once')

    def renew(token):
        try:
            sql(f"set role gather_ingestion_worker; select gather_private.renew_text_job('{job}','{token}')")
            return 'renewed'
        except subprocess.CalledProcessError as error:
            if 'stale_lease' in error.stderr:
                return 'stale'
            raise

    # New version and heartbeat both lock the same source before touching jobs.
    with ThreadPoolExecutor(max_workers=2) as pool:
        renewal = pool.submit(renew, recovered['lease_token'])
        replacement = pool.submit(enqueue, str(uuid.uuid4()))
        assert renewal.result() in ('renewed', 'stale')
        newer = replacement.result()
    assert newer != job and renew(recovered['lease_token']) == 'stale'
    assert sql(f"select state from gather_private.ingestion_jobs where id='{job}'") == 'cancelled'
    print('PASS: replacement/heartbeat race permanently fences prior version')

    active = claim(0)
    assert active and active['id'] == newer
    job = newer
    def delete():
        return sql(f"set role authenticated; set request.jwt.claim.sub='{owner}'; "
                   f"select public.request_source_deletion('{source}')")
    with ThreadPoolExecutor(max_workers=2) as pool:
        renewal = pool.submit(renew, active['lease_token'])
        deletion = pool.submit(delete)
        assert renewal.result() in ('renewed', 'stale')
        assert deletion.result() == 't'
    assert renew(active['lease_token']) == 'stale' and claim(0) is None
    assert sql(f"select count(*) from gather_private.ingestion_jobs where source_id='{source}' "
               "and (state<>'cancelled' or lease_token is not null)") == '0'
    assert sql(f"select gather_private.finish_source_cleanup('{source}')") == 't'
    print('PASS: deletion/heartbeat race leaves no active lease or derivative after cleanup')


if __name__ == '__main__':
    main()
