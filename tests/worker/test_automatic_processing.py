"""Injected providers and stores; not evidence of live cloud inference."""
import io
import subprocess
import sys
import threading
import time
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from services.worker.automatic_processing import AutomaticAdmission, AutomaticDispatcher, StartupProvider
from scripts.operator_library import PilotSession, PilotWorker, PILOT_USERS
from scripts.check_cloud_ingestion import BoundedProvider
from scripts.check_hosted_flow import cancellable_startup, wait_for_startup, PilotFailure
from services.worker.service_clients import SessionClient
from services.worker.library_session import LibraryError


class AutomaticTests(unittest.TestCase):
    def test_only_startup_429_or_503_retry_within_same_budget(self):
        from scripts.check_hosted_flow import wait_for_automatic_startup
        cancel=Mock(is_set=Mock(return_value=False))
        with patch('scripts.check_hosted_flow.wait_for_startup',side_effect=[PilotFailure('cloud_startup_http_429'),None]) as probe:
            self.assertEqual(wait_for_automatic_startup(Mock(),cancel=cancel),2)
            self.assertLessEqual(probe.call_args_list[1].kwargs['startup_timeout'],probe.call_args_list[0].kwargs['startup_timeout'])
        with patch('scripts.check_hosted_flow.wait_for_startup',side_effect=PilotFailure('cloud_startup_http_503')) as probe:
            with self.assertRaises(PilotFailure):wait_for_automatic_startup(Mock(),cancel=cancel)
            self.assertEqual(probe.call_count,3)
        with patch('scripts.check_hosted_flow.wait_for_startup',side_effect=PilotFailure('cloud_startup_http_403')) as probe:
            with self.assertRaises(PilotFailure):wait_for_automatic_startup(Mock(),cancel=cancel)
            self.assertEqual(probe.call_count,1)
    def test_model_waits_for_status_slot_within_unchanged_deadline(self):
        from services.worker import service_transport as transport
        from tests.worker.test_service_clients import Handler
        from http.server import ThreadingHTTPServer
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        server.base='http://127.0.0.1:'+str(server.server_port)
        server.received=[]
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        transport._SLOT.acquire()
        timer=threading.Timer(.1,transport._SLOT.release); timer.start()
        try:
            result=transport.request_json(server.base,'/ok',{},None,timeout=2,wait_for_slot=True)
            self.assertEqual(result,{'ok':True})
            self.assertEqual(len(server.received),1)
        finally: timer.join(); server.shutdown(); server.server_close(); thread.join(2)
        transport._SLOT.acquire()
        try:
            with self.assertRaisesRegex(transport.TransportError,'timeout'):
                transport.request_json(server.base,'/ok',{},None,timeout=.05,wait_for_slot=True)
        finally: transport._SLOT.release()

    def test_safe_model_reason_survives_ingestion_without_provider_details(self):
        from services.worker.model_availability import ModelServiceError
        from tests.worker.test_ingestion import MemoryRepository, SyntheticProvider
        from services.worker.ingestion import run_once
        provider=SyntheticProvider()
        provider.infer=Mock(side_effect=ModelServiceError('busy','model_busy'))
        result=run_once(MemoryRepository(),provider)
        self.assertEqual(result['diagnostic']['model_reason'],'model_busy')
        self.assertEqual(result['state'],'queued')

    def test_recovery_uses_verified_session_and_exact_attempt(self):
        from services.worker.library_api import validate
        source='10000000-0000-0000-0000-000000000001'
        job='20000000-0000-0000-0000-000000000001'
        api=Mock(spec=SessionClient,side_effect=[{'id':next(iter(PILOT_USERS))},True])
        dispatcher=Mock()
        session=PilotSession(api,Mock(),Mock(),dispatcher=dispatcher)
        self.assertTrue(session.process(source,job,1))
        self.assertEqual(api.call_args.args,('POST','/rest/v1/rpc/request_automatic_processing',
            {'p_source':source,'p_job':job,'p_attempts':1}))
        dispatcher.wake.assert_called_once()
        for attempt in (-1,3,True,'1'):
            with self.assertRaises(ValueError): validate('/v1/process',{'source_id':source,'job_id':job,'expected_attempts':attempt})

    def test_recovery_refusal_does_not_wake_or_accept_foreign_identity(self):
        source='10000000-0000-0000-0000-000000000001'
        api=Mock(spec=SessionClient,side_effect=[{'id':next(iter(PILOT_USERS))},False])
        dispatcher=Mock()
        session=PilotSession(api,Mock(),Mock(),dispatcher=dispatcher)
        self.assertFalse(session.process(source,source,1))
        dispatcher.wake.assert_not_called()
        api.side_effect=[{'id':source}]
        with self.assertRaises(LibraryError): session.process(source,source,1)
        dispatcher.wake.assert_not_called()

    def test_admission_uses_existing_transaction_with_intent(self):
        repo = Mock()
        AutomaticAdmission(repo).call('submit_text','fixture')
        repo.call.assert_called_once_with('submit_automatic_text','fixture')
        with self.assertRaises(ValueError): AutomaticAdmission(repo).call('claim_text_job')

    def test_unauthenticated_request_does_not_wake_dispatcher(self):
        dispatcher = Mock()
        api = Mock(spec=SessionClient,return_value={'id':'00000000-0000-0000-0000-000000000001'})
        session = PilotSession(api,Mock(),Mock(),dispatcher=dispatcher)
        with self.assertRaises(LibraryError): session.import_text(original=b'abc',media='text/plain',title='t',request_id='r')
        dispatcher.wake.assert_not_called()

    def test_uncertain_commit_wakes_durable_recovery_without_resubmitting(self):
        from scripts.operator_library import RAW
        dispatcher = Mock()
        api = Mock(spec=SessionClient,return_value={'id':next(iter(PILOT_USERS))})
        session = PilotSession(api,Mock(),Mock(),dispatcher=dispatcher)
        with patch('services.worker.library_session.submit',side_effect=RuntimeError('uncertain')) as submit:
            with self.assertRaises(LibraryError): session.import_text(original=RAW,media='text/plain',title='t',request_id='r')
        submit.assert_called_once()
        dispatcher.wake.assert_called_once()

    def test_automatic_worker_keeps_existing_owner_and_target_guards(self):
        from services.worker.worker_lifecycle import WorkerStartError
        repo = Mock()
        worker = PilotWorker(repo,'target',automatic=True,text_files=True)
        repo.call.return_value = {'id':'other','owner_id':next(iter(PILOT_USERS))}
        with self.assertRaises(WorkerStartError): worker.call('claim_text_job')
        repo.call.assert_called_once_with('claim_automatic_text_job','target')

    def test_dispatcher_recovers_pending_once_and_waits_after_failure(self):
        repo,worker = Mock(),Mock()
        repo.call.side_effect = ['job',None]
        completed = threading.Event()
        worker.run.return_value = {'outcomes':[{'state':'queued'}]}
        dispatcher = AutomaticDispatcher(repo,lambda job:worker,lambda:True,lambda *_:completed.set())
        dispatcher.start()
        try:
            self.assertTrue(completed.wait(2))
            self.assertEqual(worker.run.call_count,1)
            time.sleep(.05)
            self.assertEqual(repo.call.call_count,1)  # No retry polling.
            dispatcher.wake()
            end = time.monotonic()+1
            while repo.call.call_count<2 and time.monotonic()<end: time.sleep(.005)
            self.assertEqual(worker.run.call_count,1)
        finally: dispatcher.stop(); dispatcher.join()

    def test_duplicate_wakes_and_shutdown_do_not_duplicate_or_abandon_thread(self):
        entered,release = threading.Event(),threading.Event()
        repo,worker = Mock(),Mock()
        repo.call.side_effect=['job',None,None]
        worker.run.side_effect=lambda: (entered.set(),release.wait(2),{'outcomes':[{'state':'ready'}]})[-1]
        worker.stop.side_effect=release.set
        dispatcher=AutomaticDispatcher(repo,lambda _:worker,lambda:True)
        dispatcher.start()
        self.assertTrue(entered.wait(1))
        for _ in range(10): dispatcher.wake()
        dispatcher.stop(); dispatcher.join()
        worker.stop.assert_called_once()
        worker.run.assert_called_once()

    def test_exhausted_budget_does_not_claim_a_job(self):
        repo=Mock()
        dispatcher=AutomaticDispatcher(repo,Mock(),lambda:False)
        dispatcher.start(); time.sleep(.02); dispatcher.stop(); dispatcher.join()
        repo.call.assert_not_called()

    def test_startup_before_inference_once_and_no_inference_on_failure(self):
        inner,prepare = Mock(),Mock()
        provider=StartupProvider(inner,prepare)
        cancel=threading.Event()
        provider.infer({'role':'document'},cancel=cancel)
        provider.infer({'role':'document'},cancel=cancel)
        prepare.assert_called_once_with(cancel)
        self.assertEqual(inner.infer.call_count,2)
        inner.reset_mock()
        from services.inference.runtime import InferenceError
        with self.assertRaises(InferenceError):
            StartupProvider(inner,Mock(side_effect=RuntimeError())).infer({},cancel=cancel)
        inner.infer.assert_not_called()

    def test_startup_failure_is_retryable_and_redacted_through_real_coordinator(self):
        from tests.worker.test_ingestion import MemoryRepository, SyntheticProvider
        from services.worker.ingestion import run_once
        repo=MemoryRepository()
        inner=SyntheticProvider()
        inner.infer=Mock()
        for failure,code in ((PilotFailure('cloud_identity_unavailable'),'cloud_identity_unavailable'),
                             (RuntimeError('sensitive detail'),'startup_unavailable')):
            provider=StartupProvider(inner,Mock(side_effect=failure))
            result=run_once(repo,provider)
            self.assertEqual(result['state'],'queued')
            self.assertEqual(result['error_code'],'temporarily_unavailable')
            self.assertEqual(provider.startup_error,code)
        inner.infer.assert_not_called()

    def test_shared_provider_rejects_concurrent_inference_without_spending_extra(self):
        from services.worker.model_availability import ModelServiceError
        entered,release=threading.Event(),threading.Event()
        inner=Mock()
        inner.infer.side_effect=lambda *a,**kw:(entered.set(),release.wait(1),{})[-1]
        provider=BoundedProvider(inner)
        thread=threading.Thread(target=lambda:provider.infer({},cancel=threading.Event()))
        thread.start(); self.assertTrue(entered.wait(1))
        try:
            with self.assertRaises(ModelServiceError): provider.infer({},cancel=threading.Event())
            self.assertEqual(provider.calls,1)
        finally: release.set(); thread.join(2)

    def test_startup_cancellation_reaps_the_single_helper(self):
        cancel=threading.Event()
        timer=threading.Timer(.15,cancel.set)
        timer.start()
        start=time.monotonic()
        try:
            with self.assertRaisesRegex(PilotFailure,'cancelled'):
                cancellable_startup([sys.executable,'-c','import time; time.sleep(10)'],input=b'',
                    cwd=None,env=None,timeout=2,cancel=cancel)
            self.assertLess(time.monotonic()-start,2)
        finally: timer.cancel()

    def test_identity_timeout_is_not_misreported_as_cloud_readiness(self):
        identity=Mock()
        identity.get.side_effect=subprocess.TimeoutExpired('synthetic',5)
        with patch('scripts.check_hosted_flow.cancellable_startup') as probe,redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(PilotFailure,'cloud_identity_unavailable'):
                wait_for_startup(identity,cancel=threading.Event())
            probe.assert_not_called()
