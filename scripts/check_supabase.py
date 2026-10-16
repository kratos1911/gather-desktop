"""Local-only Auth/PostgREST/Storage integration with synthetic users and bytes.

Called by supabase_test_stack.py against a disposable stack. Never prints tokens.
Deletes only this run's generated fixtures, including when an assertion fails.
"""
from pathlib import Path
import sys
import json
import secrets
import subprocess
import uuid
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = 'gather_integration_db'
BASE = 'http://127.0.0.1:55431'
BUCKET = 'gather-originals'
HTTP = build_opener(ProxyHandler({}))


def sql(statement, expected_error=None):
    result = subprocess.run(
        ['docker', 'exec', '-i', DB, 'psql', '-X', '-At', '-U', 'postgres',
         '-v', 'ON_ERROR_STOP=1'], input=statement, capture_output=True,
        text=True, timeout=20)
    if expected_error:
        assert result.returncode != 0 and expected_error in result.stderr, 'Expected database rejection'
    elif result.returncode:
        raise RuntimeError('Local fixture database command failed')
    return result.stdout.strip()


def check(ok, label):
    if not ok:
        raise AssertionError(label)
    print('PASS:', label)


def main(config):
    for name in (DB, 'gather_integration_gateway'):
        inspected = subprocess.run(['docker', 'inspect', '--format',
            '{{json .NetworkSettings.Ports}}', name], capture_output=True,
            text=True, check=True, timeout=10)
        ports = json.loads(inspected.stdout)
        bindings = [item for values in ports.values() if values for item in values]
        if (name == DB and bindings) or (name != DB and bindings != [
                {'HostIp': '127.0.0.1', 'HostPort': '55431'}]):
            raise RuntimeError('Refusing test stack with non-loopback published ports')
    if config['API_URL'] != BASE:
        raise RuntimeError('Refusing non-test Supabase endpoint')
    anon, service = config['ANON_KEY'], config['SERVICE_ROLE_KEY']

    def request(method, path, token=None, payload=None, raw=None):
        headers = {'apikey': anon, 'Authorization': 'Bearer ' + (token or anon)}
        if raw is not None:
            data = raw
            headers['Content-Type'] = 'text/plain'
        else:
            data = None if payload is None else json.dumps(payload).encode()
            headers['Content-Type'] = 'application/json'
        req = Request(BASE + path, data=data, headers=headers, method=method)
        try:
            with HTTP.open(req, timeout=20) as response:
                return response.status, response.read(1024 * 1024)
        except HTTPError as error:
            return error.code, error.read(1024 * 1024)

    def api(method, path, token=None, payload=None, status=200):
        code, body = request(method, path, token, payload)
        if code != status:
            # Responses may contain private fixture data; keep failures bounded/content-free.
            raise RuntimeError(f'Local API {method} {path.split("?")[0]} returned {code}, expected {status}')
        return json.loads(body) if body else None

    users, sources, objects = [], [], []
    try:
        code, _ = request('POST', '/auth/v1/signup', payload={
            'email': f'gather-disabled-{uuid.uuid4().hex}@example.invalid',
            'password': secrets.token_urlsafe(24)})
        check(code in (400,403,422), 'public signup remains disabled')
        for _ in range(2):
            email = f'gather-test-{uuid.uuid4().hex}@example.invalid'
            password = secrets.token_urlsafe(24)
            user = api('POST', '/auth/v1/admin/users', service,
                       {'email': email, 'password': password, 'email_confirm': True})
            owner = str(uuid.UUID(user['id']))
            users.append(owner)
            session = api('POST', '/auth/v1/token?grant_type=password', payload={
                'email': email, 'password': password})
            token = session['access_token']
            check(api('GET', '/auth/v1/user', token)['id'] == owner, 'real Auth session resolves synthetic owner')
            sql(f"insert into gather_private.source_quotas values('{owner}',2,0)")
            key = str(uuid.uuid4())
            params = {'p_request_key': key, 'p_kind': 'file', 'p_title': 'Synthetic original'}
            source = str(uuid.UUID(api('POST', '/rest/v1/rpc/save_source', token, params)))
            sources.append((owner, source, token, params))
            path = f'{owner}/{source}/original'
            objects.append(path)
            code, _ = request('POST', f'/storage/v1/object/{BUCKET}/{path}', service,
                              raw=b'Gather synthetic original. No personal content.')
            check(code == 200, f'trusted fixture upload succeeds (HTTP {code})')

        owner, source, token, params = sources[0]
        other_token = sources[1][2]
        from check_published_api import check_published_api
        check_published_api(api, request, sql, check, sources)
        path = objects[0]
        read_path = f'/storage/v1/object/authenticated/{BUCKET}/{path}'
        check(api('POST', '/rest/v1/rpc/save_source', token, params) == source, 'RPC retry is idempotent')
        rows = api('GET', '/rest/v1/sources?select=id', token)
        check([row['id'] for row in rows] == [source], 'REST lists only own source')
        code, body = request('GET', read_path, token)
        check(code == 200 and body == b'Gather synthetic original. No personal content.', 'owner downloads exact original bytes')
        check(request('GET', read_path, other_token)[0] in (400,403,404), 'other user cannot download original')
        check(request('GET', read_path)[0] in (400,401,403,404), 'anonymous original read denied')
        check(request('GET', f'/storage/v1/object/public/{BUCKET}/{path}')[0] in (400,403,404), 'bucket has no public read')
        listed = api('POST', f'/storage/v1/object/list/{BUCKET}', other_token,
                     {'prefix': f'{owner}/{source}/', 'limit': 10})
        check(listed == [], 'other user cannot list original')
        code, _ = request('POST', f'/storage/v1/object/{BUCKET}/{owner}/{source}/extra', token, raw=b'forbidden')
        check(code in (400,401,403), 'client upload denied')
        code, _ = request('PUT', f'/storage/v1/object/{BUCKET}/{path}', token, raw=b'forbidden')
        check(code in (400,401,403), 'client overwrite denied')
        # Storage DELETE may return success with zero matched objects under RLS.
        request('DELETE', f'/storage/v1/object/{BUCKET}', token, {'prefixes': [path]})
        check(request('GET', read_path, service)[0] == 200, 'direct client delete cannot remove bytes')
        check(not api('POST', '/rest/v1/rpc/request_source_deletion', other_token,
                      {'p_source_id': source}), 'cross-owner deletion RPC rejected')
        check(api('POST', '/rest/v1/rpc/request_source_deletion', token,
                  {'p_source_id': source}), 'owner deletion RPC creates tombstone')
        check(api('GET', '/rest/v1/sources?select=id', token) == [], 'tombstone hides REST source')
        check(request('GET', read_path, token)[0] in (400,403,404), 'tombstone hides Storage original')
        sql(f"select gather_private.finish_source_cleanup('{source}')", 'storage_cleanup_pending')
        check(sql(f"select used from gather_private.source_quotas where owner_id='{owner}'") == '1',
              'missed Storage cleanup retains quota')
        check(sql(f"select count(*) from gather_private.cleanup_requests where source_id='{source}'") == '1',
              'missed Storage cleanup retains durable request')
        # API deletes actual bytes. Never delete storage.objects with SQL.
        api('DELETE', f'/storage/v1/object/{BUCKET}', service, {'prefixes': [path]})
        check(request('GET', read_path, service)[0] in (400,404), 'Storage API removal makes bytes unavailable to admin')
        check(sql(f"select count(*) from storage.objects where bucket_id='{BUCKET}' and name='{path}'") == '0',
              'Storage API removes object metadata')
        # Model a process interruption after external deletion, before SQL finalization.
        check(api('POST', '/rest/v1/rpc/request_source_deletion', token, {'p_source_id': source}),
              'deletion request survives interruption after external removal')
        api('DELETE', f'/storage/v1/object/{BUCKET}', service, {'prefixes': [path]})
        check(sql(f"select used from gather_private.source_quotas where owner_id='{owner}'") == '1',
              'repeated external removal does not prematurely release quota')
        check(sql(f"select gather_private.finish_source_cleanup('{source}')") == 't', 'database cleanup succeeds after Storage removal')
        check(sql(f"select gather_private.finish_source_cleanup('{source}')") == 'f', 'repeated cleanup is harmless')
        check(sql(f"select used from gather_private.source_quotas where owner_id='{owner}'") == '0', 'cleanup releases quota once')
        check(api('POST', '/rest/v1/rpc/save_source', token, params) == source
              and api('GET', '/rest/v1/sources?select=id', token) == [], 'late save retry cannot resurrect deleted source')
        other_path = f'/storage/v1/object/authenticated/{BUCKET}/{objects[1]}'
        check(request('GET', other_path, other_token)[0] == 200, 'other owner original survives cleanup')
        check(request('GET', '/rest/v1/sources', 'invalid-token')[0] == 401, 'invalid JWT rejected')
        print('Local Auth/REST/Storage checks passed. Desktop and concurrent upload fencing remain pending.')
    finally:
        # Exact generated IDs only, no reset/truncate and no unrelated data touched.
        for path in objects:
            api('DELETE', f'/storage/v1/object/{BUCKET}', service, {'prefixes': [path]})
        for owner, source, _, _ in sources:
            sql(f"begin; set local role authenticated; set local request.jwt.claim.sub='{owner}'; "
                f"select public.request_source_deletion('{source}'); commit; "
                f"select gather_private.finish_source_cleanup('{source}');")
        for owner in users:
            sql(f"delete from gather_private.save_receipts where owner_id='{owner}'; "
                f"delete from gather_private.source_quotas where owner_id='{owner}';")
            api('DELETE', f'/auth/v1/admin/users/{owner}', service)
        print('Synthetic users, sources, receipts, quotas and objects cleaned up.')


if __name__ == '__main__':
    raise SystemExit('Run scripts/supabase_test_stack.py to create an isolated test stack.')
