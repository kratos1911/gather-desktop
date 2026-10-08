"""Disposable PostgreSQL ownership checks. No host ports, volumes or real data."""
from pathlib import Path
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'postgres@sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24'


def run(*args, input=None, timeout=60):
    return subprocess.run(['docker', *args], input=input, text=True,
                          capture_output=True, check=True, timeout=timeout)


def main():
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
                 ROOT / 'tests/database/ownership.sql']
        for path in files:
            result = run('exec', '-i', name, 'psql', '-X', '-U', 'postgres',
                         '-v', 'ON_ERROR_STOP=1', input=path.read_text(encoding='utf-8'))
            print(path.relative_to(ROOT))
            for line in result.stderr.splitlines():
                if 'PASS:' in line:
                    print(line)
        print('Database ownership checks passed. Auth/Storage services were not tested.')
    except subprocess.CalledProcessError as error:
        print(error.stderr)
        raise
    finally:
        # Exact random task container only. No global prune or shared services.
        run('rm', '-f', '-v', name)


if __name__ == '__main__':
    main()
