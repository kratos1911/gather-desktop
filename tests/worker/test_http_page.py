import base64
import json
import unittest
import threading
from unittest.mock import Mock

from services.worker.extractor_runner import run_job
from services.worker.bookmark_pipeline import BookmarkPipeline
from services.worker.fetch_broker import BrokerError
from services.worker.restricted_fetch import FetchedPage


class HttpPageTests(unittest.TestCase):
    def job(self, body=b'<article><h1>Local title</h1><p>Waterproof jacket</p></article>', content_type='text/html'):
        return {'backend': 'http-page', 'source_id': 'local', 'url': 'https://public.example/start',
                'notes': 'My note', 'backend_version': 'restricted-http-v1', 'fetched_at': '2026-10-08T12:00:00Z',
                'result': {'body_base64': base64.b64encode(body).decode(), 'content_type': content_type,
                           'final_url': 'https://public.example/end', 'redirects': 1}}

    def test_html_provenance_notes_and_deterministic_revision(self):
        raw = json.dumps(self.job()).encode()
        first = json.loads(run_job(raw))
        self.assertEqual(first, json.loads(run_job(raw)))
        doc = first['document']
        self.assertIn('Waterproof jacket', doc['fields']['page_text'])
        self.assertEqual(doc['fields']['notes'], 'My note')
        self.assertEqual(doc['fetch']['final_url'], 'https://public.example/end')
        self.assertEqual(doc['fetch']['backend'], 'restricted-http-v1')
        self.assertFalse(doc['semantic_ready'])
        self.assertTrue(any(c['field'] == 'page_text' for c in doc['chunks']))

    def test_plain_text_is_not_interpreted_as_html(self):
        output = json.loads(run_job(json.dumps(self.job(b'Use <tag> literally', 'text/plain')).encode()))
        self.assertEqual(output['document']['fields']['page_text'], 'Use <tag> literally')

    def test_bad_base64_oversize_and_unknown_fields_fail_safely(self):
        for change in [{'body_base64': '!!!'}, {'body_base64': base64.b64encode(b'x'*65537).decode()},
                       {'command': 'fixture-secret'}, {'redirects': -1}, {'content_type': 'video/mp4'}]:
            job = self.job(); job['result'].update(change)
            output = run_job(json.dumps(job).encode())
            self.assertEqual(json.loads(output)['status'], 'error')
            self.assertNotIn(b'fixture-secret', output)

    def test_pipeline_connects_actual_bytes_without_claiming_crawl4ai(self):
        pipeline = BookmarkPipeline('sha256:'+'a'*64)
        pipeline.broker = Mock()
        pipeline.broker.fetch.return_value = FetchedPage('https://public.example/end', 'text/html', b'<p>jacket</p>', 1)
        pipeline.parser = Mock()
        pipeline.parser.run.side_effect = lambda raw, **_: json.loads(run_job(raw))
        output = pipeline.process('local', 'https://public.example/start', notes='My note')
        self.assertEqual(output['document']['fields']['page_text'], 'jacket')
        self.assertFalse(output['document']['semantic_ready'])

    def test_fetch_failure_never_calls_parser(self):
        pipeline = BookmarkPipeline('sha256:'+'a'*64)
        pipeline.broker = Mock(); pipeline.parser = Mock()
        pipeline.broker.fetch.side_effect = BrokerError('FETCH_TIMEOUT')
        with self.assertRaisesRegex(BrokerError, 'FETCH_TIMEOUT'):
            pipeline.process('local', 'https://public.example', notes='Preserve in caller')
        pipeline.parser.run.assert_not_called()

    def test_cancel_between_fetch_and_parse_does_not_publish_passages(self):
        pipeline = BookmarkPipeline('sha256:'+'a'*64)
        pipeline.broker = Mock(); pipeline.parser = Mock()
        cancel = threading.Event()
        def fetched(*args, **kwargs):
            cancel.set()
            return FetchedPage('https://public.example', 'text/html', b'<p>fixture</p>', 0)
        pipeline.broker.fetch.side_effect = fetched
        with self.assertRaisesRegex(BrokerError, 'FETCH_CANCELLED'):
            pipeline.process('local', 'https://public.example', cancel=cancel)
        pipeline.parser.run.assert_not_called()
