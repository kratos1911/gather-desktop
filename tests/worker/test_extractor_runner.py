import json
import unittest
from services.worker.extractor_runner import run_job, MAX_INPUT


class RunnerTests(unittest.TestCase):
    def job(self):
        return {'backend':'crawl4ai', 'source_id':'a', 'url':'https://example.com',
                'result':{'success':True, 'status_code':200, 'url':'https://example.com', 'markdown':'A jacket'},
                'backend_version':'fixture', 'fetched_at':'2026-09-30T00:00:00Z'}

    def test_valid_output_job(self):
        result = json.loads(run_job(json.dumps(self.job()).encode()))
        self.assertEqual(result['status'], 'processed')
        self.assertEqual(result['document']['fields']['page_text'], 'A jacket')
        self.assertFalse(result['document']['semantic_ready'])

    def test_bad_payloads_fail_safely(self):
        for payload in [b'bad', b'[]', b'{}', b'\xff', b'x'*(MAX_INPUT+1), b'{"backend":1,"backend":2}']:
            with self.subTest(payload=payload[:20]):
                self.assertEqual(json.loads(run_job(payload))['status'], 'error')

    def test_unknown_options_and_backends_rejected(self):
        for update in [{'command':'secret-command'}, {'backend':'shell'}, {'backend':[]}]:
            job = self.job(); job.update(update)
            result = run_job(json.dumps(job).encode())
            self.assertEqual(json.loads(result)['status'], 'error')
            self.assertNotIn(b'secret-command', result)

    def test_failed_upstream_keeps_notes(self):
        job = self.job(); job.update(result={'success':False}, notes='Remember')
        result = json.loads(run_job(json.dumps(job).encode()))
        self.assertEqual(result['document']['fields']['notes'], 'Remember')
