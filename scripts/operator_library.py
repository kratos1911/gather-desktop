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

from scripts.check_hosted_flow import configuration, google_token, wait_for_startup, PilotFailure, BASE, RAW, QUERY, ExpectedWorker
from scripts.pilot_capacity import warm_instance, CapacityError
from scripts.check_cloud_ingestion import IDENTITY, BoundedProvider
from services.worker.cloud_provider import cloud_provider
from services.worker.database_transport import DatabaseRepository, ROOT
from services.worker.local_credentials import database_config
from services.worker.library_api import LibraryAPI
from services.worker.library_session import LibrarySession, LibraryError, identifier
from services.worker.service_clients import SessionClient
from services.worker.worker_lifecycle import WorkerRun, WorkerStartError
from services.worker.ingestion import parse
from services.inference.chunking import chunk_document

PILOT_USERS = frozenset(('8b8de9a3-6600-465d-9ae6-8a0f2271c1dc',
                         '903b7ed0-9d21-467c-907a-4032d589f4c4'))


class PilotSession(LibrarySession):
    def __init__(self, *args, text_files=False):
        super().__init__(*args)
        self.text_files = text_files

    def _owner(self):
        owner = super()._owner()
        if owner not in PILOT_USERS:
            raise LibraryError('session_unavailable')
        return owner

    def _validate_import_scope(self, original, media, confirm_cloud_storage):
        if original == RAW and media == 'text/plain' and confirm_cloud_storage is False:
            return
        if not self.text_files:
            raise LibraryError('file_import_disabled')
        if confirm_cloud_storage is not True:
            raise LibraryError('file_confirmation_required')
        try:
            parse(original,media)
            chunks = chunk_document(original.decode('utf-8'),self._provider.count_tokens)
        except Exception:
            raise LibraryError('file_invalid') from None
        # The operator provider already permits only three calls per process.
        # Reject before storing a file that cannot fit a fresh worker's budget.
        if len(chunks)>3:
            raise LibraryError('file_exceeds_pilot_budget')

    def search(self, query, *, limit=20, cancel=None):
        self._owner()
        if not self.text_files and query != QUERY:
            raise LibraryError('pilot_fixture_only')
        return super().search(query,limit=limit,cancel=cancel)


class PilotWorker(ExpectedWorker):
    def __init__(self, *args, text_files=False):
        super().__init__(*args)
        self.text_files = text_files

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
        if function == 'read_job_original' and not self.text_files and value != RAW.hex():
            raise ValueError('pilot_fixture_only')
        return value


class RefreshingPilotToken:
    """Mint a fresh, explicitly scoped invoker token for each model request.

    The long-running localhost API must not keep one hour-long CLI token in its
    memory for the lifetime of the browser session. Tokens are not cached or
    written to disk; gcloud account/project/caller/audience remain pinned.
    """
    config = IDENTITY

    def get(self, *, cancel=None, timeout=5):
        if cancel is not None and cancel.is_set():
            raise PilotFailure('cancelled')
        token = google_token(timeout=timeout)
        try:
            return token.get(cancel=cancel,timeout=timeout)
        finally:
            token.invalidate()

    def invalidate(self):
        # No token is cached across requests.
        return None


def run_ready_worker(worker, identity):
    """Use the approved run-scoped capacity guard before spending a job attempt."""
    with warm_instance():
        wait_for_startup(identity,wait_for_capacity=True)
        return worker.run()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--serve',action='store_true')
    action.add_argument('--work',action='store_true')
    parser.add_argument('--job-id')
    parser.add_argument('--text-files',action='store_true',help='Private two-account TXT/Markdown pilot; explicit storage confirmation, no automatic worker.')
    args = parser.parse_args()
    if args.work:
        identifier(args.job_id)
    elif args.job_id:
        parser.error('--job-id requires --work')
    if not args.serve and not args.work:
        print('Preview: --serve binds 127.0.0.1:8765; --work --job-id UUID warms and checks readiness before claiming one exact pilot job, then restores minimum zero. Two pilot accounts only; fixed synthetic content by default. --text-files explicitly enables reviewed TXT/Markdown and custom queries. At most 3 real model calls per process. No automatic retry.')
        return
    # Fail before secrets or cloud identity if the runtime is unsuitable.
    if args.serve and (version('uvicorn')!='0.54.0' or version('h11')!='0.16.0'):
        raise ValueError('unverified_server_dependencies')
    import psycopg2  # noqa: F401: installed driver prerequisite, no connection.
    role = 'gather_worker' if args.work else 'gather_admission'
    config = replace(database_config(role),connect_timeout=10)
    key = configuration()
    identity = RefreshingPilotToken() if args.serve else google_token()
    try:
        provider = BoundedProvider(cloud_provider(IDENTITY,ROOT/'output/inference-model',token_provider=identity))
        if args.work:
            repository = PilotWorker(DatabaseRepository(config,operation_timeout=15),args.job_id,text_files=args.text_files)
            worker = WorkerRun(repository,provider)
            previous = {sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
            try:
                for sig in previous:
                    signal.signal(sig,lambda *_:worker.stop())
                result = run_ready_worker(worker,identity)
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
                    lambda owner:DatabaseRepository(config,owner=owner,operation_timeout=15),provider,text_files=args.text_files)
            app = LibraryAPI(session)
            mode = 'reviewed private TXT/Markdown' if args.text_files else 'fixed synthetic pilot content'
            print('Operator API: http://127.0.0.1:8765; '+mode+' only. Ctrl+C stops admission. Worker is a separate command.',flush=True)
            create_server(app,operator_origin='http://localhost:1420').run()
    finally:
        identity.invalidate()


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit('Operator process stopped.') from None
    except Exception as error:
        code = str(error) if isinstance(error,(CapacityError,PilotFailure)) else 'operator_library_failed'
        raise SystemExit(code+'. No automatic retry; no secrets or provider details printed.') from None
