import threading
import io
import json
from urllib.error import HTTPError, URLError
import unittest
from unittest.mock import Mock, patch, MagicMock

from scripts.check_hosted_flow import QueryCapture, ExpectedWorker, PilotFailure, exercise, RAW, wait_for_startup, sign_in_clients, main, reviewed_import_receipt, PROJECT, ready_child
from services.worker.service_transport import TransportError
from services.worker.library_session import LibraryError
from services.worker.ingestion_repository import RepositoryError
from scripts.check_hosted_flow import reviewed_cleanup_receipt


class HostedFlowTests(unittest.TestCase):
    def test_controlplane_wait_and_http_probe_share_startup_deadline(self):
        result = Mock(returncode=0,stdout=b'{"ready":true}')
        identity = Mock(get=Mock(return_value='synthetic'))
        with patch('scripts.pilot_capacity.wait_ready') as wait, patch(
                'scripts.check_hosted_flow.time.monotonic',side_effect=[100,145]), patch(
                'scripts.check_hosted_flow.subprocess.run',return_value=result) as run, patch('builtins.print'):
            wait_for_startup(identity,wait_for_capacity=True)
        wait.assert_called_once_with(160)
        self.assertEqual(run.call_args.kwargs['timeout'],15)

    def test_cleanup_restart_requires_cancelled_zero_inference_fixture(self):
        original = dict(project=PROJECT,request_id='69c36bc2-dd02-4a44-98b0-43055e9d3f38',
            source_id='5a4c1c59-9313-4982-a1b4-c8dd73dd30c1',
            job_id='7ecced47-982e-45fb-ad77-301f56a46ffe',
            version_id='d81c5f32-674b-48fd-b6d0-9a12973844a2',
            passed=False,stage='processing',tombstoned=True,real_model_requests=0)
        for changes in ({},{'passed':True},{'tombstoned':False},{'real_model_requests':1},
                        {'project':'foreign'},{'source_id':'bad'},{'stage':'search_open'}):
            path = MagicMock()
            path.open.return_value.__enter__.return_value = io.BytesIO(json.dumps(original|changes).encode())
            if changes:
                with self.assertRaises(PilotFailure):
                    reviewed_cleanup_receipt(path)
            else:
                self.assertEqual(reviewed_cleanup_receipt(path)['source_id'],original['source_id'])

    def test_readiness_http_error_has_status_without_body_or_token(self):
        error = HTTPError('https://fixture.run.app/ready',429,'private description',{},io.BytesIO(b'private body'))
        error.read = Mock(side_effect=AssertionError('must not read error body'))
        output = Mock(buffer=io.BytesIO())
        with patch('sys.stdin',Mock(buffer=io.BytesIO(b'synthetic-token'))), patch('sys.stdout',output), patch(
                'urllib.request.build_opener') as opener, patch('builtins.print') as printed:
            opener.return_value.open.side_effect = error
            with self.assertRaises(SystemExit):
                ready_child()
        self.assertEqual(json.loads(printed.call_args.args[0]),{'ready':False,'http_status':429})
        error.read.assert_not_called()

    def test_readiness_network_timeout_is_specific_and_private(self):
        with patch('sys.stdin',Mock(buffer=io.BytesIO(b'synthetic-token'))), patch(
                'urllib.request.build_opener') as opener, patch('builtins.print') as printed:
            opener.return_value.open.side_effect = URLError(TimeoutError('private details'))
            with self.assertRaises(SystemExit):
                ready_child()
        self.assertEqual(json.loads(printed.call_args.args[0]),{'ready':False,'error':'network_timeout'})

    def test_resume_reuses_only_eligible_unacknowledged_import(self):
        original = dict(project=PROJECT,request_id='69c36bc2-dd02-4a44-98b0-43055e9d3f38',
                        passed=False,stage='import',real_model_requests=0)
        for changes in ({},{'stage':'processing'},{'source_id':'acknowledged'},
                        {'real_model_requests':1},{'passed':True},{'resumed_import':True}):
            path = MagicMock()
            path.open.return_value.__enter__.return_value = io.BytesIO(json.dumps(original|changes).encode())
            if changes:
                with self.assertRaises(PilotFailure):
                    reviewed_import_receipt(path)
            else:
                self.assertEqual(reviewed_import_receipt(path)['request_id'],original['request_id'])

    def test_private_database_reason_survives_only_as_safe_receipt_metadata(self):
        first,second = self.fixtures()
        error = LibraryError('import_failed')
        error.__context__ = RepositoryError('temporarily_unavailable',reason='operation_deadline_exceeded')
        first.import_text.side_effect = error
        receipt = {'request_id':'request','passed':False}
        with self.assertRaises(LibraryError):
            exercise(first,second,Mock(),Mock(),receipt,Mock())
        self.assertEqual(receipt['database_reason'],'operation_deadline_exceeded')
        self.assertEqual(receipt['failure_code'],'import_failed')
        first.delete.assert_not_called()

    def test_worker_wrapper_preserves_explicit_cleanup_bound(self):
        wrapped = ExpectedWorker(Mock(cleanup_wait_seconds=16),'job')
        self.assertEqual(wrapped.cleanup_wait_seconds,16)

    def test_startup_http_status_is_safe_and_not_retried(self):
        result = Mock(returncode=1,stdout=b'{"ready":false,"http_status":429}')
        with patch('scripts.check_hosted_flow.subprocess.run',return_value=result) as run, patch('builtins.print'):
            with self.assertRaisesRegex(PilotFailure,'^cloud_startup_http_429$'):
                wait_for_startup(Mock(get=Mock(return_value='synthetic')))
        self.assertEqual(run.call_count,1)

    def test_startup_only_never_authenticates_users_or_imports(self):
        identity = Mock()
        with patch('sys.argv',['pilot','--check-startup']), patch(
                'scripts.check_hosted_flow.google_token',return_value=identity), patch(
                'scripts.check_hosted_flow.wait_for_startup') as ready, patch(
                'scripts.check_hosted_flow.sign_in_clients') as signin, patch(
                'scripts.check_hosted_flow.database_config') as db, patch('builtins.print'):
            main()
        ready.assert_called_once_with(identity)
        signin.assert_not_called()
        db.assert_not_called()
        identity.invalidate.assert_called_once()

    def test_signin_preserves_safe_code_and_never_returns_error_body(self):
        with patch('scripts.check_hosted_flow.getpass.getpass',return_value='synthetic-password'), patch(
                'scripts.check_hosted_flow.request_json',side_effect=TransportError('auth_invalid_credentials')):
            with self.assertRaisesRegex(PilotFailure,'^pilot_a_auth_invalid_credentials$'):
                sign_in_clients('synthetic-public-key')

    def test_auth_only_does_not_access_db_or_cloud_or_import(self):
        with patch('sys.argv',['pilot','--check-auth']), patch(
                'scripts.check_hosted_flow.configuration',return_value='fixture'), patch(
                'scripts.check_hosted_flow.request_json',return_value={'disable_signup':True}), patch(
                'scripts.check_hosted_flow.sign_in_clients',return_value=[Mock(),Mock()]), patch(
                'scripts.check_hosted_flow.database_config') as db, patch(
                'scripts.check_hosted_flow.google_token') as google, patch(
                'scripts.check_hosted_flow.exercise') as run, patch('builtins.print'):
            main()
            db.assert_not_called()
            google.assert_not_called()
            run.assert_not_called()

    def test_startup_probe_keeps_token_off_arguments_and_has_separate_deadline(self):
        identity = Mock()
        identity.get.return_value = 'synthetic-token'
        result = Mock(returncode=0,stdout=b'{"ready":true}')
        with patch('scripts.check_hosted_flow.subprocess.run',return_value=result) as run, patch('builtins.print'):
            wait_for_startup(identity)
        self.assertNotIn('synthetic-token',repr(run.call_args.args))
        self.assertEqual(run.call_args.kwargs['input'],b'synthetic-token')
        self.assertEqual(run.call_args.kwargs['timeout'],60)

    def test_failed_startup_has_no_automatic_retry(self):
        result = Mock(returncode=1,stdout=b'')
        with patch('scripts.check_hosted_flow.subprocess.run',return_value=result) as run, patch('builtins.print'):
            with self.assertRaises(PilotFailure):
                wait_for_startup(Mock(get=Mock(return_value='synthetic')))
        self.assertEqual(run.call_count,1)

    def test_replays_only_identical_real_query_and_honors_cancellation(self):
        source = Mock()
        source.infer.return_value = {'real_response_fixture':True}
        provider = QueryCapture(source)
        request = {'role':'query','texts':['same query']}
        first = provider.infer(request,cancel=None)
        self.assertIs(provider.infer(request,cancel=None),first)
        self.assertEqual(source.infer.call_count,1)
        self.assertEqual(provider.replays,1)
        with self.assertRaises(PilotFailure):
            provider.infer({'role':'query','texts':['different query']},cancel=None)
        cancel = threading.Event()
        cancel.set()
        with self.assertRaises(PilotFailure):
            provider.infer(request,cancel=cancel)

    def test_unexpected_job_is_not_processed(self):
        worker = Mock()
        worker.call.return_value = {'id':'unrelated'}
        with self.assertRaises(PilotFailure):
            ExpectedWorker(worker,'expected').call('claim_text_job')
        self.assertEqual(worker.call.call_count,1)

    def fixtures(self):
        first,second = Mock(),Mock()
        item = {'source_id':'source','version_id':'version','job_id':'job'}
        first.import_text.return_value = item
        first.status.side_effect = [[{'state':'queued'}],[{'state':'ready'}],[]]
        first.open.side_effect = [[{'body':RAW.decode()}],[]]
        first.search.side_effect = [{'windows':[{'source_id':'source'}]},{'windows':[]}]
        first.delete.return_value = True
        second.status.return_value = []
        second.open.return_value = []
        second.delete.return_value = False
        second.search.return_value = {'windows':[]}
        return first,second

    def test_complete_flow_marks_visibility_success_but_cleanup_pending(self):
        first,second = self.fixtures()
        receipt = {'request_id':'request','passed':False}
        with patch('scripts.check_hosted_flow.run_once',return_value={'state':'ready','version_id':'version'}):
            exercise(first,second,Mock(),Mock(),receipt,Mock())
        self.assertTrue(receipt['passed'])
        self.assertTrue(receipt['tombstoned'])
        self.assertTrue(receipt['cleanup_pending'])
        first.delete.assert_called_once_with('source')

    def test_failure_tombstones_source_without_claiming_success(self):
        first,second = self.fixtures()
        first.search.side_effect = RuntimeError('synthetic failure')
        receipt = {'request_id':'request','passed':False}
        with patch('scripts.check_hosted_flow.run_once',return_value={'state':'ready','version_id':'version'}):
            with self.assertRaises(RuntimeError):
                exercise(first,second,Mock(),Mock(),receipt,Mock())
        self.assertFalse(receipt['passed'])
        self.assertTrue(receipt['tombstoned'])
        first.delete.assert_called_once_with('source')

    def test_unknown_submission_outcome_remains_explicit(self):
        first,second = self.fixtures()
        first.import_text.side_effect = RuntimeError('uncertain commit')
        receipt = {'request_id':'request','passed':False}
        with self.assertRaises(RuntimeError):
            exercise(first,second,Mock(),Mock(),receipt,Mock())
        self.assertEqual(receipt['cleanup_pending'],'unknown_until_submission_acknowledged')
        first.delete.assert_not_called()


if __name__=='__main__':
    unittest.main()
