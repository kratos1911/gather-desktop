"""Opt-in Gather pilot: real cloud vectors, disposable SQL and TEST-ONLY auth shim.

Run as a module. Token arrives via stdin, never arguments, files or reports.
No hosted user data, production DB credentials or model weights are loaded.
"""
import argparse
import json
import subprocess
import sys
import time
import uuid

from scripts.check_database import IMAGE, ROOT, run
from services.worker.cloud_identity import IdentityConfig, _claims
from services.worker.cloud_provider import cloud_provider
from services.worker.ingestion import submit, run_once
from services.worker.ingestion_repository import FUNCTIONS, RepositoryError
from services.worker.search import search
from services.worker.service_transport import TransportError, credential, request_json

AUDIENCE = 'https://gather-inference-pilot-119730530113.asia-south1.run.app'
CALLER = 'gather-pilot-caller@gather-development-511211.iam.gserviceaccount.com'
IDENTITY = IdentityConfig(AUDIENCE, CALLER, ('serviceAccount:'+CALLER,))


class PilotToken:
    """Explicit developer credential; no refresh, metadata or shared-secret fallback.

    Claim checks reject mistakes; Google IAM and receiving verifier authenticate.
    """
    config = IDENTITY

    def __init__(self, token):
        credential(token)
        if len(token) > 7168:
            raise TransportError('invalid_identity_token')
        self.expiry = _claims(token, self.config, time.time())
        self.deadline = time.monotonic() + self.expiry - time.time() - 60
        self._token = token

    def invalidate(self):
        self._token = None

    def get(self, *, cancel=None, timeout=5):
        if cancel is not None and cancel.is_set():
            raise TransportError('cancelled')
        if not self._token or time.time()+60 >= self.expiry or time.monotonic() >= self.deadline:
            self.invalidate()
            raise TransportError('identity_unavailable')
        return self._token


class BoundedProvider:
    def __init__(self, provider):
        self.provider, self.calls = provider, 0
        self.count_tokens = provider.count_tokens

    def infer(self, request, *, cancel):
        if self.calls >= 3:
            raise RuntimeError('pilot_request_budget_exhausted')
        self.calls += 1  # Failures count too; never retry.
        return self.provider.infer(request, cancel=cancel)


def literal(value):
    if value is None:
        return 'null'
    if type(value) is bytes:
        return "decode('"+value.hex()+"','hex')"
    if type(value) is int:
        return str(value)
    if isinstance(value, (dict, list)):
        value = json.dumps(value, allow_nan=False)
    return "'"+str(value).replace("'", "''")+"'"


def check_flow(sql, provider):
    """SQL transport is a fixture, NOT Supabase Auth/PostgREST verification."""
    owner, other = str(uuid.uuid4()), str(uuid.uuid4())
    sql(f"insert into auth.users values('{owner}'),('{other}'); "
        f"insert into gather_private.source_quotas values('{owner}',2,0)")

    def scoped(statement, role='authenticated', who=owner):
        return sql(f"set role {role}; set request.jwt.claim.sub='{who}'; "+statement)

    class Repository:
        def __init__(self, role):
            self.role = role

        def call(self, function, *args):
            if function not in FUNCTIONS or len(args) != FUNCTIONS[function]:
                raise RepositoryError('invalid_input')
            try:
                return json.loads(scoped('select to_jsonb(gather_private.'+function+
                    '('+','.join(map(literal, args))+'))', self.role))
            except subprocess.CalledProcessError:
                raise RepositoryError('temporarily_unavailable') from None

    def rows(function, args, who=owner):
        return json.loads(scoped('select coalesce(jsonb_agg(to_jsonb(r)),\'[]\'::jsonb) from public.'+
            function+'('+','.join(map(literal, args))+') r', who=who))

    def api(method, path, payload=None):
        if (method, path, payload) == ('GET', '/auth/v1/user', None):
            return {'id': owner}  # TEST ONLY trusted-context shim.
        if method == 'POST' and path == '/rest/v1/rpc/search_published_text':
            return rows('search_published_text', [payload[k] for k in
                ('p_query','p_model','p_revision','p_dimensions','p_limit')])
        if method == 'POST' and path == '/rest/v1/rpc/open_published_text':
            return rows('open_published_text', [payload['p_source'],payload['p_version']])
        raise ValueError('invalid_test_route')

    raw = b'Gather synthetic pilot note: database security uses ownership checks and row-level policies.'
    admission, worker = Repository('gather_ingestion_coordinator'), Repository('gather_ingestion_worker')
    key = str(uuid.uuid4())
    def add():
        return submit(admission, request_id=key, title='Synthetic cloud pilot', original=raw, media='text/plain')
    item = add()
    assert add() == item, 'duplicate submission changed identity'
    result = run_once(worker, provider)
    if result['state'] != 'ready':
        print('Ingestion outcome: '+json.dumps({k:result[k] for k in ('state','error_code') if k in result}))
        raise RuntimeError('cloud_ingestion_not_ready')
    context = search('How do we restrict access to database records?', api=api, provider=provider)
    assert len(context['windows']) == 1, 'published result missing'
    window = context['windows'][0]
    assert window['source_id'] == item['source_id'], 'wrong source returned'
    opened = rows('open_published_text', [item['source_id'],result['version_id']])
    assert len(opened) == 1 and opened[0]['body'] == raw.decode(), 'source read mismatch'
    assert rows('open_published_text', [item['source_id'],result['version_id']], other) == [], 'owner isolation failed'
    scoped('select public.request_source_deletion('+literal(item['source_id'])+')')
    assert rows('open_published_text', [item['source_id'],result['version_id']]) == [], 'deleted source readable'
    # Reuse stored real document vector for visibility check: no fourth model call.
    vector = json.loads(sql('select embedding::text from gather_private.staged_passages limit 1'))
    from services.inference.runtime import MODEL, REVISION, DIMENSIONS
    assert rows('search_published_text',[vector,MODEL,REVISION,DIMENSIONS,20]) == [], 'deleted source searchable'
    scoped('select gather_private.finish_source_cleanup('+literal(item['source_id'])+')', 'postgres')
    return {'ready': True, 'duplicate_safe': True, 'search_open_delete': True,
            'owner_sql_isolation': True, 'cloud_requests': provider.calls,
            'authentication_scope': 'real cloud IAM; local SQL Auth shim, not user JWT',
            'quality_scope': 'one synthetic source; not retrieval-quality evaluation'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='Explicitly allow up to three cloud requests')
    args = parser.parse_args()
    if not args.run:
        print('Preview only: local disposable SQL, tokenizer only, up to 3 real cloud requests; token via stdin.')
        return
    name = 'gather-cloud-pilot-'+uuid.uuid4().hex
    created = False
    token = None
    stage = 'credentials'
    try:
        token = PilotToken(sys.stdin.readline(8194).strip())
        provider = BoundedProvider(cloud_provider(IDENTITY, ROOT/'output/inference-model', token_provider=token))
        stage = 'local_preflight'
        run('info', '--format', '{{.ServerVersion}}', timeout=15)
        run('image', 'inspect', IMAGE, timeout=10)  # Never implicitly pull an image.
        stage = 'cloud_readiness'
        value = token.get()
        ready = request_json(AUDIENCE,'/ready',{'Authorization':'Bearer '+value,
            'X-Serverless-Authorization':'Bearer '+value},None,timeout=15)
        del value
        if ready != {'ready':True}:
            raise RuntimeError('cloud_not_ready')
        stage = 'database_startup'
        run('run','--detach','--name',name,'--network','none','--memory','256m','--cpus','1',
            '--pids-limit','100','--tmpfs','/var/lib/postgresql/data:rw,size=192m,uid=100,gid=101',
            '--user','100:101','--env','PGHOST=/tmp','--mount',
            f'type=bind,source={ROOT / "tests/database/start-postgres.sh"},target=/gather-start.sh,readonly',
            '--entrypoint','sh',IMAGE,'/gather-start.sh')
        created = True
        for _ in range(30):
            try:
                run('exec',name,'pg_isready','-U','postgres',timeout=5)
                break
            except subprocess.CalledProcessError:
                time.sleep(.5)
        else:
            raise RuntimeError('pilot_database_unavailable')
        def sql(statement):
            return run('exec','-i',name,'psql','-X','-qAt','-U','postgres','-v','ON_ERROR_STOP=1',
                input="set statement_timeout='5s'; set lock_timeout='3s'; "+statement, timeout=10).stdout.strip()
        sql('\n'.join(p.read_text(encoding='utf-8') for p in
            [ROOT/'tests/database/bootstrap.sql', *sorted((ROOT/'supabase/migrations').glob('*.sql'))]))
        stage = 'ingestion_search_open_delete'
        evidence = check_flow(sql, provider)
        evidence['observed_at_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        (ROOT/'output/cloud-ingestion-pilot.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
        print(json.dumps(evidence,indent=2))
    except Exception as error:
        evidence = {'passed':False,'stage':stage,
            'error_code':str(error) if isinstance(error,TransportError) else 'pilot_check_failed',
            'cloud_requests':provider.calls if 'provider' in locals() else 0}
        (ROOT/'output/cloud-ingestion-failure.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
        print(json.dumps(evidence))
        raise
    finally:
        if token is not None:
            token.invalidate()
        if created:
            run('rm','-f','-v',name)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('Pilot failed; no automatic retry. Inspect locally; no credentials or provider bodies printed.',file=sys.stderr)
        sys.exit(1)
