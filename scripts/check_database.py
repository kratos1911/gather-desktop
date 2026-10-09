"""Disposable PostgreSQL ownership checks. No host ports, volumes or real data."""
from pathlib import Path
import subprocess
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'postgres@sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24'


def run(*args, input=None, timeout=60):
    return subprocess.run(['docker', *args], input=input, text=True,
                          capture_output=True, check=True, timeout=timeout)


def main():
    # Fail clearly before creating anything if Docker is unavailable.
    run('info', '--format', '{{.ServerVersion}}', timeout=15)
    name = 'gather-db-check-' + uuid.uuid4().hex
    try:
        run('run', '--detach', '--name', name, '--network', 'none',
            '--memory', '256m', '--cpus', '1', '--pids-limit', '100',
            '--tmpfs', '/var/lib/postgresql/data:rw,size=192m',
            '--env', 'POSTGRES_HOST_AUTH_METHOD=trust', IMAGE)
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
                 ROOT / 'tests/database/ownership.sql',
                 ROOT / 'tests/database/lifecycle.sql']
        result = run('exec', '-i', name, 'psql', '-X', '-U', 'postgres',
                     '-v', 'ON_ERROR_STOP=1', input='\n'.join(
                         path.read_text(encoding='utf-8') for path in files))
        for line in result.stderr.splitlines():
            if 'PASS:' in line:
                print(line)
        concurrency_checks(name)
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


if __name__ == '__main__':
    main()
