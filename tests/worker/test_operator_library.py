import unittest
import io
import json
import tempfile
from contextlib import redirect_stdout, nullcontext, contextmanager
from pathlib import Path
from unittest.mock import Mock, patch

from scripts.operator_library import PilotSession, PilotWorker, PILOT_USERS, RefreshingPilotToken, main, RAW, QUERY, run_ready_worker
from services.worker.library_session import LibraryError
from services.worker.service_clients import SessionClient
from services.worker.worker_lifecycle import WorkerRun, WorkerStartError
from services.worker.database_transport import DatabaseConfig, ROOT


class OperatorTests(unittest.TestCase):
    def test_file_pilot_requires_server_opt_in_and_per_file_confirmation(self):
        api = Mock(spec=SessionClient,return_value={'id':next(iter(PILOT_USERS))})
        factory,provider = Mock(),Mock()
        provider.count_tokens.side_effect = lambda text: len(text)
        values = dict(original=b'# Synthetic file\r\nNotes.',media='text/markdown',request_id='id',title='note.md')
        for enabled,confirmed,code in ((False,True,'file_import_disabled'),(True,False,'file_confirmation_required')):
            with self.assertRaisesRegex(LibraryError,'^'+code+'$'):
                PilotSession(api,factory,provider,text_files=enabled).import_text(**values,confirm_cloud_storage=confirmed)
        factory.assert_not_called()
        provider.infer.assert_not_called()
        with patch('services.worker.library_session.submit',return_value={'state':'queued'}) as submit:
            PilotSession(api,factory,provider,text_files=True).import_text(**values,confirm_cloud_storage=True)
            self.assertEqual(submit.call_args.kwargs['original'],values['original'])
            self.assertNotIn('confirm_cloud_storage',submit.call_args.kwargs)
        provider.infer.assert_not_called()

    def test_private_file_validation_and_pilot_budget_run_before_admission(self):
        api = Mock(spec=SessionClient,return_value={'id':next(iter(PILOT_USERS))})
        factory,provider = Mock(),Mock()
        provider.count_tokens.side_effect = lambda text: len(text)
        library = PilotSession(api,factory,provider,text_files=True)
        for raw,media,code in ((b'\x00binary','text/plain','file_invalid'),(b'\xff','text/plain','file_invalid'),
            (b'valid','text/html','file_invalid'),(b'x'*65537,'text/plain','file_invalid'),
            (b'word '*500,'text/markdown','file_exceeds_pilot_budget')):
            with self.subTest(code=code),self.assertRaisesRegex(LibraryError,'^'+code+'$'):
                library.import_text(original=raw,media=media,title='test',request_id='id',confirm_cloud_storage=True)
        factory.assert_not_called()
        provider.infer.assert_not_called()

    def test_enabled_file_mode_keeps_owner_and_worker_target_guards(self):
        api = Mock(spec=SessionClient,return_value={'id':'00000000-0000-0000-0000-000000000001'})
        provider = Mock()
        with self.assertRaisesRegex(LibraryError,'session_unavailable'):
            PilotSession(api,Mock(),provider,text_files=True).import_text(original=b'file',media='text/plain',title='t',request_id='id',confirm_cloud_storage=True)
        provider.count_tokens.assert_not_called()
        repo = Mock()
        repo.call.return_value = {'id':'other-job','owner_id':next(iter(PILOT_USERS))}
        with self.assertRaisesRegex(WorkerStartError,'different_job_claimed'):
            PilotWorker(repo,'job',text_files=True).call('claim_text_job')
        repo.call.return_value = {'id':'job','owner_id':'foreign'}
        with self.assertRaisesRegex(WorkerStartError,'pilot_user_only'):
            PilotWorker(repo,'job',text_files=True).call('claim_text_job')

    def test_api_token_is_minted_and_discarded_for_each_request(self):
        cancel = __import__('threading').Event()
        first,second=Mock(),Mock()
        first.get.return_value='token-one'
        second.get.return_value='token-two'
        with patch('scripts.operator_library.google_token',side_effect=[first,second]) as mint:
            provider=RefreshingPilotToken()
            self.assertEqual(provider.get(cancel=cancel,timeout=4),'token-one')
            self.assertEqual(provider.get(cancel=cancel,timeout=4),'token-two')
        self.assertEqual(mint.call_count,2)
        for token in (first,second):
            token.get.assert_called_once_with(cancel=cancel,timeout=4)
            token.invalidate.assert_called_once_with()
        self.assertEqual(provider.invalidate(),None)

    def test_api_token_does_not_mint_after_cancellation(self):
        cancel=__import__('threading').Event(); cancel.set()
        with patch('scripts.operator_library.google_token') as mint:
            with self.assertRaisesRegex(Exception,'cancelled'):
                RefreshingPilotToken().get(cancel=cancel)
            mint.assert_not_called()

    def test_readiness_precedes_claim_and_restores_capacity(self):
        events = []
        @contextmanager
        def warm():
            events.append('warm')
            try: yield
            finally: events.append('restore')
        worker = Mock()
        worker.run.side_effect = lambda: events.append('claim') or {'outcomes':[{'state':'ready'}]}
        with patch('scripts.operator_library.warm_instance',warm), patch('scripts.operator_library.wait_for_startup',side_effect=lambda *a,**kw:events.append('ready')):
            run_ready_worker(worker,Mock())
        self.assertEqual(events,['warm','ready','claim','restore'])

    def test_startup_and_worker_failures_both_restore_capacity(self):
        for startup_failure in (True,False):
            restored=[]
            @contextmanager
            def warm():
                try: yield
                finally: restored.append(True)
            worker=Mock()
            worker.run.side_effect=RuntimeError('synthetic failure')
            with patch('scripts.operator_library.warm_instance',warm), patch('scripts.operator_library.wait_for_startup',side_effect=RuntimeError('not ready') if startup_failure else None):
                with self.assertRaises(RuntimeError): run_ready_worker(worker,Mock())
            self.assertEqual(restored,[True])
            if startup_failure: worker.run.assert_not_called()

    def test_worker_refuses_foreign_owner_and_nonfixture_original(self):
        repo = Mock()
        worker = PilotWorker(repo,'job')
        repo.call.return_value = {'id':'job','owner_id':'foreign'}
        with self.assertRaisesRegex(WorkerStartError,'pilot_user_only'):
            worker.call('claim_text_job')
        repo.call.return_value = b'personal'.hex()
        with self.assertRaisesRegex(ValueError,'pilot_fixture_only'):
            worker.call('read_job_original','job','lease')

    def test_idle_and_wrong_job_are_distinct_without_processing(self):
        repo,provider = Mock(),Mock()
        worker = PilotWorker(repo,'job')
        repo.call.return_value = None
        self.assertEqual(WorkerRun(worker,provider).run()['outcomes'],[{'state':'idle'}])
        repo.call.assert_called_once_with('claim_target_text_job','job')
        repo.call.return_value = {'id':'other-job','owner_id':next(iter(PILOT_USERS))}
        result = WorkerRun(worker,provider).run()['outcomes'][0]
        self.assertEqual(result['error_code'],'different_job_claimed')
        provider.infer.assert_not_called()

    def test_worker_receipt_and_failure_exit_code(self):
        job = '00000000-0000-0000-0000-000000000001'
        config = DatabaseConfig('127.0.0.1',5432,'gather_worker','synthetic',test_loopback=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'output') as folder, patch('scripts.operator_library.warm_instance',return_value=nullcontext()), patch('scripts.operator_library.wait_for_startup'):
            with patch('scripts.operator_library.ROOT',Path(folder)), patch('scripts.operator_library.database_config',return_value=config), patch('scripts.operator_library.configuration',return_value='public'), patch('scripts.operator_library.google_token') as token, patch('scripts.operator_library.cloud_provider'), patch('scripts.operator_library.WorkerRun') as run, patch('sys.argv',['operator_library','--work','--job-id',job]):
                for state,expected in (('unavailable',1),('ready',0)):
                    run.return_value.run.return_value={'stopped':False,'outcomes':[{'state':state}]}
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(main(),expected)
                files = list((Path(folder)/'output/operator-pilot').glob('worker-*.json'))
                self.assertEqual(len(files),2)
                for path in files:
                    receipt = json.loads(path.read_text())
                    self.assertEqual(receipt['requested_job_id'],job)
                    self.assertEqual(receipt['real_model_requests'],0)
                self.assertEqual(token.return_value.invalidate.call_count,2)
    def test_preview_has_no_secret_or_network_work(self):
        with patch('sys.argv',['operator_library']), patch('scripts.operator_library.google_token') as token, patch('scripts.operator_library.database_config') as config:
            main()
            token.assert_not_called()
            config.assert_not_called()

    def test_non_pilot_user_rejected_for_reads_and_search(self):
        api = Mock(spec=SessionClient,return_value={'id':'00000000-0000-0000-0000-000000000001'})
        provider = Mock()
        library = PilotSession(api,Mock(),provider)
        for action in (lambda:library.status('id'),lambda:library.search(QUERY)):
            with self.assertRaises(LibraryError): action()
        provider.infer.assert_not_called()
        self.assertTrue(all(c.args[1]=='/auth/v1/user' for c in api.call_args_list))

    def test_personal_content_and_arbitrary_queries_rejected(self):
        api = Mock(spec=SessionClient,return_value={'id':next(iter(PILOT_USERS))})
        factory,provider = Mock(),Mock()
        library = PilotSession(api,factory,provider)
        with self.assertRaises(LibraryError): library.import_text(original=b'personal',media='text/plain',request_id='id',title='Synthetic refusal')
        with self.assertRaises(LibraryError): library.search('arbitrary query')
        factory.assert_not_called()
        provider.infer.assert_not_called()

    def test_fixed_fixture_reuses_existing_admission(self):
        api = Mock(spec=SessionClient,return_value={'id':next(iter(PILOT_USERS))})
        library = PilotSession(api,Mock(),Mock())
        with patch('services.worker.library_session.submit',return_value={'state':'queued'}) as submit:
            library.import_text(original=RAW,media='text/plain',request_id='id',title='Synthetic')
            self.assertEqual(submit.call_args.kwargs['original'],RAW)
