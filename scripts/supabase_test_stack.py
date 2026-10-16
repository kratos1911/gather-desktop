"""Run the real Supabase core APIs on an isolated disposable local test stack."""
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import build_opener, ProxyHandler

import check_supabase

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ['docker', 'compose', '-f', str(ROOT / 'compose.supabase-test.yaml')]


def token(secret, role):
    def encode(value):
        return base64.urlsafe_b64encode(json.dumps(value, separators=(',', ':')).encode()).rstrip(b'=')
    body = encode({'alg': 'HS256', 'typ': 'JWT'}) + b'.' + encode({
        'role': role, 'iss': 'gather-local-test', 'iat': int(time.time()),
        'exp': int(time.time()) + 3600})
    signature = base64.urlsafe_b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).rstrip(b'=')
    return (body + b'.' + signature).decode()


def main():
    secret = secrets.token_urlsafe(48)
    config = {'API_URL': check_supabase.BASE,
              'ANON_KEY': token(secret, 'anon'), 'SERVICE_ROLE_KEY': token(secret, 'service_role')}
    env = dict(os.environ, GATHER_TEST_JWT=secret, GATHER_TEST_ANON=config['ANON_KEY'],
               GATHER_TEST_SERVICE=config['SERVICE_ROLE_KEY'])
    def compose(*args):
        result = subprocess.run([*COMPOSE, *args], cwd=ROOT, env=env,
                                capture_output=True, text=True, timeout=120)
        if result.returncode:
            diagnostic = result.stderr[-3000:]
            for value in (secret, config['ANON_KEY'], config['SERVICE_ROLE_KEY']):
                diagnostic = diagnostic.replace(value, '[redacted]')
            raise RuntimeError('Disposable Supabase stack command failed: ' + args[0] + '\n' + diagnostic)
    # Never adopt a different run's stack or destroy its state.
    existing = subprocess.run(['docker', 'ps', '-aq', '--filter',
        'label=com.docker.compose.project=gather-supabase-test'],
        capture_output=True, text=True, check=True, timeout=15)
    if existing.stdout.strip():
        raise RuntimeError('A gather-supabase-test stack already exists; inspect it before retrying')
    startup_complete = False
    try:
        compose('up', '-d')
        http = build_opener(ProxyHandler({}))
        for path in ('/auth/v1/health', '/storage/v1/status'):
            for attempt in range(60):
                try:
                    with http.open(check_supabase.BASE + path, timeout=2) as response:
                        if response.status == 200:
                            break
                except (HTTPError, URLError, TimeoutError):
                    pass
                time.sleep(0.5)
            else:
                raise RuntimeError('Local service did not become ready: ' + path)
        startup_complete = True
        for migration in sorted((ROOT / 'supabase/migrations').glob('*.sql')):
            check_supabase.sql(migration.read_text(encoding='utf-8'))
        check_supabase.sql("notify pgrst, 'reload schema'")
        # Wait for PostgREST's asynchronous schema cache refresh, not a guessed delay.
        for attempt in range(40):
            try:
                with http.open(check_supabase.BASE + '/rest/v1/', timeout=2) as response:
                    schema = json.load(response)
                    if '/rpc/save_source' in schema.get('paths', {}):
                        break
            except (HTTPError, URLError, TimeoutError):
                pass
            time.sleep(0.25)
        # Anonymous OpenAPI can omit protected functions, so the functional tests
        # remain the final readiness/authorization proof.
        check_supabase.main(config)
    except Exception:
        if not startup_complete:
            # Capture bounded startup evidence before cleanup, before fixture users
            # or document requests exist. Never print credentials from container logs.
            diagnostic = subprocess.run([*COMPOSE,'logs','--no-color','--tail','35','db','auth','storage','gateway'],
                cwd=ROOT,env=env,capture_output=True,text=True,timeout=20)
            logs = diagnostic.stdout + diagnostic.stderr
            for value in (secret,config['ANON_KEY'],config['SERVICE_ROLE_KEY']):
                logs = logs.replace(value,'[redacted]')
            target = ROOT / 'output/database-checks/supabase-startup.log'
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(logs,encoding='utf-8')
            print('Startup diagnostics saved under output/database-checks/supabase-startup.log')
        raise
    finally:
        compose('down', '--volumes')
        print('Disposable Supabase stack removed; no test data retained.')


if __name__ == '__main__':
    main()
