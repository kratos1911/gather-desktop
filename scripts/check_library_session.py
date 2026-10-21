"""Real local Auth/PostgREST boundary; synthetic embeddings and psql admission.

Called only by the existing disposable stack. Not a hosted DB driver test.
"""
import base64
import json
import uuid

from services.worker.ingestion import run_once
from services.worker.ingestion_repository import FUNCTIONS, RepositoryError
from services.worker.library_session import LibrarySession, LibraryError
from tests.worker.test_ingestion import SyntheticProvider


def check_library_sessions(sql, check, sources, session_factory):
    owner, _, token, _ = sources[0]
    other, _, other_token, _ = sources[1]

    def literal(value):
        if value is None:
            return 'null'
        if type(value) is bytes:
            return "decode('"+value.hex()+"','hex')"
        if type(value) is int:
            return str(value)
        if isinstance(value, (dict,list)):
            value = json.dumps(value,allow_nan=False)
        return "'"+str(value).replace("'","''")+"'"

    class Repository:
        # Test transport only. Actual session ownership comes from Auth via LibrarySession.
        def __init__(self, verified_owner=None):
            self.owner = str(uuid.UUID(verified_owner)) if verified_owner else ''
            self.role = 'gather_ingestion_coordinator' if verified_owner else 'gather_ingestion_worker'

        def call(self, function, *args):
            assert function in FUNCTIONS and len(args) == FUNCTIONS[function]
            try:
                result = sql(f"set role {self.role}; set request.jwt.claim.sub='{self.owner}'; "
                    "set statement_timeout='5s'; set lock_timeout='3s'; "
                    'select to_jsonb(gather_private.'+function+'('+','.join(map(literal,args))+'))')
                return json.loads(result.splitlines()[-1])
            except Exception:
                raise RepositoryError('temporarily_unavailable') from None

    class CountingProvider(SyntheticProvider):
        calls = 0

        def infer(self, request, *, cancel):
            self.calls += 1
            return super().infer(request, cancel=cancel)

    provider = CountingProvider()
    identities = []
    def admission(verified_owner):
        identities.append(verified_owner)
        return Repository(verified_owner)
    first = LibrarySession(session_factory(token), admission, provider)
    second = LibrarySession(session_factory(other_token), admission, provider)
    key, created = str(uuid.uuid4()), None
    args = dict(request_id=key,title='Synthetic authenticated import',
                original=b'Local synthetic text for authenticated library checks.',media='text/plain')
    try:
        # A well-shaped JWT with a forged subject must fail actual Auth verification.
        parts = token.split('.')
        claims = json.loads(base64.urlsafe_b64decode(parts[1]+'='*((-len(parts[1]))%4)))
        claims['sub'] = other
        parts[1] = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip('=')
        forged = LibrarySession(session_factory('.'.join(parts)), admission, provider)
        for operation in (lambda: forged.import_text(**args), lambda: forged.search('test')):
            try:
                operation()
                raise AssertionError('forged session accepted')
            except LibraryError:
                pass
        check(identities == [] and provider.calls == 0,'library rejects forged session before admission/inference')
        created = first.import_text(**args)
        check(first.import_text(**args) == created,'authenticated import replay is idempotent')
        check(identities == [owner,owner],'admission identity derived from real Auth response')
        sid, vid = created['source_id'],created['version_id']
        check(first.status(sid)[0]['state']=='queued','owner sees queued job through session RPC')
        check(second.status(sid)==[],'other session cannot read job status')
        check(first.open(sid,vid)==[],'unpublished import remains unreadable')
        check(second.delete(sid) is False,'other session cannot delete import')
        check(run_once(Repository(),provider)['state']=='ready','authenticated submission processes through existing coordinator')
        check(first.status(sid)[0]['state']=='ready','session reports actual ready state')
        check(first.open(sid,vid)[0]['body']==args['original'].decode(),'session opens exact published source')
        check(second.open(sid,vid)==[],'other session cannot open published source')
        check(any(w['source_id']==sid for w in first.search('test')['windows']),'session search includes published own source')
        check(all(w['source_id']!=sid for w in second.search('test')['windows']),'session search excludes another owner source')
        try:
            second.import_text(**(args | {'request_id':str(uuid.uuid4()),'source_id':sid}))
            raise AssertionError('foreign replacement accepted')
        except LibraryError:
            check(True,'foreign replacement is rejected by database ownership')
        check(first.delete(sid) is True,'owner session creates deletion tombstone')
        check(first.open(sid,vid)==[] and first.status(sid)==[],'deletion hides source and job status immediately')
        check(all(w['source_id']!=sid for w in first.search('test')['windows']),'deletion hides session search results')
    finally:
        if created:
            first.delete(created['source_id'])
            sql("select gather_private.finish_source_cleanup("+literal(created['source_id'])+")")
    print('Library session checks passed: real local JWT/Auth/RLS; synthetic vectors; test psql admission.')
