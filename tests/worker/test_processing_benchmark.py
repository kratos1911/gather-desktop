"""Synthetic HTTP controls for the opt-in operator comparison; no live calls."""
import unittest
from unittest.mock import Mock,patch
from scripts.benchmark_processing import fixture_source,run_sample,Stopped,BODY,SHA,TITLE

ID='00000000-0000-0000-0000-000000000001'


class BenchmarkControls(unittest.TestCase):
    def test_fixture_identity_is_checked_before_any_replacement(self):
        source={'source_id':ID,'title':TITLE,'state':'ready','processing_version_id':ID,'published_version_id':ID}
        for body,digest in ((BODY,SHA),('private changed body',SHA),(BODY,'0'*64)):
            with self.subTest(changed=body!=BODY or digest!=SHA):
                send=Mock(side_effect=[{'items':[source],'next_cursor':None},
                                       [{'body':body,'source_sha256':digest}]])
                with patch('scripts.benchmark_processing.call',send):
                    if body==BODY and digest==SHA:self.assertEqual(fixture_source('synthetic'),source)
                    else:
                        with self.assertRaises(Stopped):fixture_source('synthetic')
                self.assertEqual([c.args[1] for c in send.call_args_list],['list','open'])

    def test_uncertain_import_preserves_request_and_is_never_replayed(self):
        receipt={'samples':[]};save=Mock()
        with patch('scripts.benchmark_processing.call',side_effect=RuntimeError('uncertain')) as send:
            with self.assertRaises(RuntimeError):
                run_sample('synthetic',{'source_id':ID},b'fixture','baseline',1,'revision',receipt,save)
        self.assertEqual(send.call_count,1)
        self.assertEqual(receipt['samples'][0]['stage'],'import')
        self.assertEqual(send.call_args.args[2]['request_id'],receipt['samples'][0]['request_id'])

    def test_failed_job_stops_without_recovery_or_another_embedding_request(self):
        receipt={'samples':[]}
        responses=[{'source_id':ID,'job_id':ID,'version_id':ID,'automatic_processing':True},
                   [{'job_id':ID,'version_id':ID,'state':'queued','attempts':1}]]
        with patch('scripts.benchmark_processing.call',side_effect=responses) as send:
            with self.assertRaisesRegex(Stopped,'processing_requires_explicit_recovery'):
                run_sample('synthetic',{'source_id':ID},b'fixture','baseline',1,'revision',receipt,Mock())
        self.assertEqual([c.args[1] for c in send.call_args_list],['import','status'])
        self.assertEqual(receipt['samples'][0]['job_id'],ID)

    def test_completed_version_is_opened_exactly_without_search_or_delete(self):
        receipt={'samples':[]}
        responses=[{'source_id':ID,'job_id':ID,'version_id':ID,'automatic_processing':True},
                   [{'job_id':ID,'version_id':ID,'state':'ready','attempts':1}],
                   [{'body':BODY,'source_sha256':SHA,'passages':[{'id':'fixture'}]}]]
        with patch('scripts.benchmark_processing.call',side_effect=responses) as send,patch(
            'scripts.benchmark_processing.collect_logs',return_value={'classification':'synthetic'}):
            run_sample('synthetic',{'source_id':ID},b'fixture','optimized',1,'revision',receipt,Mock())
        self.assertEqual([c.args[1] for c in send.call_args_list],['import','status','open'])
        self.assertEqual(send.call_args.args[2],{'source_id':ID,'version_id':ID})
        self.assertTrue(receipt['samples'][0]['exact_open_verified'])

    def test_ack_recovery_keeps_request_identity_and_does_not_claim_repaired_wall_time(self):
        request='00000000-0000-0000-0000-000000000002'
        receipt={'samples':[{'mode':'baseline','sample':1,'stage':'import','request_id':request,
                            'started_utc':'2026-11-01T00:00:00Z','ready':False}]}
        responses=[{'source_id':ID,'job_id':ID,'version_id':ID,'automatic_processing':True},
                   [{'job_id':ID,'version_id':ID,'state':'ready','attempts':1}],
                   [{'body':BODY,'source_sha256':SHA,'passages':[{'id':'fixture'}]}]]
        with patch('scripts.benchmark_processing.call',side_effect=responses) as send,patch(
            'scripts.benchmark_processing.collect_logs',return_value={'classification':'synthetic'}):
            run_sample('synthetic',{'source_id':ID,'published_version_id':ID},b'fixture',
                       'baseline',1,'revision',receipt,Mock(),recover_ack=True)
        self.assertEqual(len(receipt['samples']),1)
        self.assertEqual(send.call_args_list[0].args[2]['request_id'],request)
        self.assertIsNone(receipt['samples'][0]['observed_seconds'])
        self.assertTrue(receipt['samples'][0]['harness_interrupted'])
        self.assertEqual([c.args[1] for c in send.call_args_list],['import','status','open'])


if __name__=='__main__':unittest.main()
