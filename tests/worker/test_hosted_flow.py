import threading
import unittest
from unittest.mock import Mock, patch

from scripts.check_hosted_flow import QueryCapture, ExpectedWorker, PilotFailure, exercise, RAW, wait_for_startup


class HostedFlowTests(unittest.TestCase):
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
