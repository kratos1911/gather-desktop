"""Explicit operator-only pilot entry points. Preview by default; no model loads.

The server binds loopback and accepts only the existing two synthetic Auth users.
An opt-in dispatcher processes only durably enrolled new imports outside HTTP requests.
"""
import argparse
from dataclasses import replace
from importlib.metadata import version
import signal
import json
from uuid import uuid4

from scripts.check_hosted_flow import configuration, google_token, wait_for_startup, wait_for_automatic_startup, PilotFailure, BASE, RAW, QUERY, ExpectedWorker
from scripts.pilot_capacity import warm_instance, CapacityError
from scripts.check_cloud_ingestion import IDENTITY, BoundedProvider
from services.worker.cloud_provider import cloud_provider
from services.worker.cloud_identity import MetadataTokenProvider
from services.worker.database_transport import DatabaseRepository, ROOT
from services.worker.local_credentials import database_config
from services.worker.library_api import LibraryAPI
from services.worker.library_session import LibrarySession, LibraryError, identifier
from services.worker.service_clients import SessionClient
from services.worker.worker_lifecycle import WorkerRun, WorkerStartError
from services.worker.ingestion import parse
from services.inference.chunking import chunk_document
from services.worker.automatic_processing import AutomaticAdmission, AutomaticDispatcher, StartupProvider

PILOT_USERS = frozenset(('8b8de9a3-6600-465d-9ae6-8a0f2271c1dc',
                         '903b7ed0-9d21-467c-907a-4032d589f4c4'))


class PilotSession(LibrarySession):
    def __init__(self, *args, text_files=False, dispatcher=None):
        super().__init__(*args)
        self.text_files = text_files
        self.dispatcher = dispatcher

    def import_text(self, **values):
        try:
            return super().import_text(**values)
        finally:
            # Even an uncertain response may have committed its durable marker.
            if self.dispatcher is not None and getattr(self,'verified_pilot',False): self.dispatcher.wake()

    def process(self, source_id, job_id, expected_attempts):
        if self.dispatcher is None: raise LibraryError('operation_failed')
        result = super().process(source_id,job_id,expected_attempts)
        if result: self.dispatcher.wake()
        return result

    def list_sources(self, **values):
        result=super().list_sources(**values)
        if self.dispatcher is not None:
            try:
                pending=self._api('POST','/rest/v1/rpc/list_source_cleanup',{})
                if type(pending) is not list or len(pending)>20: raise ValueError()
                ids=[identifier(row['source_id']) for row in pending if type(row) is dict and set(row)=={'source_id'}]
                if len(ids)!=len(pending) or len(set(ids))!=len(ids): raise ValueError()
                return dict(result,cleanup_source_ids=ids)
            except Exception: raise LibraryError('library_unavailable') from None
        return result

    def _owner(self):
        owner = super()._owner()
        if owner not in PILOT_USERS:
            raise LibraryError('session_unavailable')
        self.verified_pilot = True
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
    def __init__(self, *args, text_files=False, automatic=False):
        super().__init__(*args)
        self.text_files = text_files
        self.automatic = automatic
        self.cleanup_wait_seconds = getattr(self.worker,'cleanup_wait_seconds',6)

    def call(self, function, *args):
        value = (self.worker.call('claim_automatic_text_job' if self.automatic else 'claim_target_text_job',self.job_id)
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


class RefreshingPilotToken(MetadataTokenProvider):
    """Reuse the existing expiry/skew/locking cache with a pinned operator mint.

    Short-lived tokens remain only in memory, expire early and are discarded on
    authentication rejection/shutdown. HTTP refresh still has its five-second cap.
    """
    def __init__(self):
        super().__init__(IDENTITY)

    def _request_token(self, *, cancel=None, timeout=5):
        if cancel is not None and cancel.is_set():
            raise PilotFailure('cancelled')
        token = google_token(timeout=timeout)
        try:
            return token.get(cancel=cancel,timeout=timeout)
        finally:
            token.invalidate()

def run_ready_worker(worker, identity):
    """Use the approved run-scoped capacity guard before spending a job attempt."""
    with warm_instance():
        wait_for_startup(identity,wait_for_capacity=True)
        return worker.run()


def compose_pilot(config,worker_config,provider,identity,key,*,text_files=False,automatic=False,record=None):
    """Shared trusted composition for operator and explicit managed-cloud startup."""
    dispatcher=None
    if automatic:
        repository=DatabaseRepository(worker_config,operation_timeout=15)
        def create_worker(job):
            return WorkerRun(PilotWorker(repository,job,text_files=text_files,automatic=True),
                StartupProvider(provider,lambda cancel:wait_for_automatic_startup(identity,cancel=cancel)))
        def local_record(job,result):
            target=ROOT/'output/operator-pilot'/('automatic-'+uuid4().hex+'.json')
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(json.dumps({'job_id':job,'result':result,
                'process_model_requests':provider.calls},indent=2),encoding='utf-8')
            print('Automatic processing: '+','.join(r['state'] for r in result['outcomes']),flush=True)
        dispatcher=AutomaticDispatcher(repository,create_worker,lambda:provider.calls<3,record or local_record)
    def session(token,cancel):
        def admission(owner):
            repo=DatabaseRepository(config,owner=owner,operation_timeout=15)
            return AutomaticAdmission(repo) if dispatcher is not None else repo
        return PilotSession(SessionClient(BASE,key,token,cancel=cancel),admission,provider,
            text_files=text_files,dispatcher=dispatcher)
    return LibraryAPI(session,dispatcher=dispatcher)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--serve',action='store_true')
    action.add_argument('--work',action='store_true')
    parser.add_argument('--job-id')
    parser.add_argument('--text-files',action='store_true',help='Private two-account TXT/Markdown pilot; explicit storage confirmation, no automatic worker.')
    parser.add_argument('--auto-process',action='store_true',help='Process new imports using durable opt-in markers. Requires migrations 10/11; no automatic inference retries.')
    args = parser.parse_args()
    if args.work:
        identifier(args.job_id)
    elif args.job_id:
        parser.error('--job-id requires --work')
    if args.auto_process and args.work:
        parser.error('--auto-process is a server option')
    if not args.serve and not args.work:
        print('Preview: --serve binds 127.0.0.1:8765; --work --job-id UUID warms and checks readiness before claiming one exact pilot job, then restores minimum zero. Two pilot accounts only; fixed synthetic content by default. --text-files enables reviewed TXT/Markdown and custom queries. --auto-process enrolls only new imports; migration 10 required. At most 3 real model calls per process, shared by automatic processing and search. No automatic retry.')
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
        if args.serve and args.auto_process:
            # Existing operator setup budget, before accepting HTTP requests.
            # Subsequent HTTP identity operations still get at most five seconds.
            identity.get(timeout=15)
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
            worker_config=replace(database_config('gather_worker'),connect_timeout=10) if args.auto_process else None
            app=compose_pilot(config,worker_config,provider,identity,key,text_files=args.text_files,automatic=args.auto_process)
            mode = 'reviewed private TXT/Markdown' if args.text_files else 'fixed synthetic pilot content'
            print('Operator API: http://127.0.0.1:8765; '+mode+' only. '+
                ('New imports process automatically; 3 shared model attempts, no capacity changes.' if app.dispatcher else 'Worker is a separate command.'),flush=True)
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
