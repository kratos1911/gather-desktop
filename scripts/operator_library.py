"""Explicit operator-only pilot entry points. Preview by default; no model loads.

The server binds loopback and accepts only the existing two synthetic Auth users.
No worker starts in an HTTP request. Work runs separately for an explicit job ID.
"""
import argparse
from dataclasses import replace
from importlib.metadata import version
import signal
import json
from uuid import uuid4

from scripts.check_hosted_flow import configuration, google_token, BASE, RAW, QUERY, ExpectedWorker
from scripts.check_cloud_ingestion import IDENTITY, BoundedProvider
from services.worker.cloud_provider import cloud_provider
from services.worker.database_transport import DatabaseRepository, ROOT
from services.worker.local_credentials import database_config
from services.worker.library_api import LibraryAPI
from services.worker.library_session import LibrarySession, LibraryError, identifier
from services.worker.service_clients import SessionClient
from services.worker.worker_lifecycle import WorkerRun, WorkerStartError

PILOT_USERS = frozenset(('8b8de9a3-6600-465d-9ae6-8a0f2271c1dc',
                         '903b7ed0-9d21-467c-907a-4032d589f4c4'))


class PilotSession(LibrarySession):
    def _owner(self):
        owner = super()._owner()
        if owner not in PILOT_USERS:
            raise LibraryError('session_unavailable')
        return owner

    def import_text(self, **values):
        if values.get('original') != RAW or values.get('media') != 'text/plain':
            raise LibraryError('pilot_fixture_only')
        return super().import_text(**values)

    def search(self, query, *, limit=20, cancel=None):
        self._owner()
        if query != QUERY:
            raise LibraryError('pilot_fixture_only')
        return super().search(query,limit=limit,cancel=cancel)


class PilotWorker(ExpectedWorker):
    def call(self, function, *args):
        value = (self.worker.call('claim_target_text_job',self.job_id)
                 if function == 'claim_text_job' else self.worker.call(function,*args))
        if function == 'claim_text_job':
            if value is None:
                return None  # No eligible claim is idle, not a transport error.
            if value.get('id') != self.job_id:
                raise WorkerStartError('different_job_claimed')
            if value.get('owner_id') not in PILOT_USERS:
                raise WorkerStartError('pilot_user_only')
        if function == 'read_job_original' and value != RAW.hex():
            raise ValueError('pilot_fixture_only')
        return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--serve',action='store_true')
    action.add_argument('--work',action='store_true')
    parser.add_argument('--job-id')
    args = parser.parse_args()
    if args.work:
        identifier(args.job_id)
    elif args.job_id:
        parser.error('--job-id requires --work')
    if not args.serve and not args.work:
        print('Preview: --serve binds 127.0.0.1:8765; --work --job-id UUID handles one claimed pilot job. Synthetic pilot users/content only; each process permits at most 3 real model calls. No automatic warm capacity or retries.')
        return
    # Fail before secrets or cloud identity if the runtime is unsuitable.
    if args.serve and (version('uvicorn')!='0.54.0' or version('h11')!='0.16.0'):
        raise ValueError('unverified_server_dependencies')
    import psycopg2  # noqa: F401: installed driver prerequisite, no connection.
    role = 'gather_worker' if args.work else 'gather_admission'
    config = replace(database_config(role),connect_timeout=10)
    key = configuration()
    identity = google_token()
    try:
        provider = BoundedProvider(cloud_provider(IDENTITY,ROOT/'output/inference-model',token_provider=identity))
        if args.work:
            repository = PilotWorker(DatabaseRepository(config,operation_timeout=15),args.job_id)
            worker = WorkerRun(repository,provider)
            previous = {sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
            try:
                for sig in previous:
                    signal.signal(sig,lambda *_:worker.stop())
                result = worker.run()
                print('Worker states: '+','.join(r['state'] for r in result['outcomes']))
                receipt = {'requested_job_id':args.job_id, 'result':result,
                           'real_model_requests':provider.calls}
                target = ROOT/'output/operator-pilot'/('worker-'+args.job_id+'-'+uuid4().hex+'.json')
                target.parent.mkdir(parents=True,exist_ok=True)
                with target.open('x',encoding='utf-8') as stream:
                    json.dump(receipt,stream,indent=2)
                print(json.dumps(receipt))
                print('Safe worker receipt: '+str(target))
                return 0 if result['outcomes'] and result['outcomes'][-1]['state']=='ready' else 1
            finally:
                for sig,handler in previous.items(): signal.signal(sig,handler)
        else:
            from services.worker.library_server import create_server
            def session(token,cancel):
                return PilotSession(SessionClient(BASE,key,token,cancel=cancel),
                    lambda owner:DatabaseRepository(config,owner=owner,operation_timeout=15),provider)
            app = LibraryAPI(session)
            print('Operator API: http://127.0.0.1:8765; fixed synthetic pilot content only. Ctrl+C stops admission. Worker is a separate command.')
            create_server(app,operator_origin='http://localhost:1420').run()
    finally:
        identity.invalidate()


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit('operator_library_failed. No automatic retry; no secrets or provider details printed.') from None
