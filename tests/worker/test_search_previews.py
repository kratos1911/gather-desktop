"""Synthetic request boundaries for the compact search path."""
import unittest

from services.worker.search import SearchError, search
from tests.worker.test_search import Provider, Session


class SearchPreviewTests(unittest.TestCase):
    def setUp(self):
        self.session = Session(2)
        self.provider = Provider()
        first, second = self.session.rows
        first = dict(first, media_type='application/pdf', locations=[2], similarity=.1)
        second = dict(second, media_type='text/plain', locations=[], similarity=.2)
        self.batch = {'semantic': [second, first], 'keywords': [first]}

    def api(self, method, path, payload=None):
        if path.endswith('search_published_previews'):
            self.session.calls.append((method, path, payload))
            return self.batch
        if path != '/auth/v1/user' and not path.endswith('/list_library_sources'):
            raise AssertionError('unexpected remote read')
        return self.session(method, path, payload)

    def test_one_database_ranking_request_with_no_reader_reads(self):
        result = search('cedar', api=self.api, provider=self.provider, compact=True)
        self.assertEqual([call[1].rsplit('/', 1)[-1] for call in self.session.calls],
                         ['user', 'list_library_sources', 'search_published_previews'])
        self.assertEqual(len(self.provider.calls), 1)
        self.assertEqual(result['version'], 'search-previews-v1')
        self.assertEqual(len(result['windows']), 1)
        hit = result['windows'][0]
        self.assertEqual((hit['pages'], hit['start'], hit['end']), ([2], 8, 17))
        self.assertEqual(hit['text'], self.batch['keywords'][0]['body'])
        self.assertEqual(result['utf8_bytes'], len(hit['text'].encode('utf-8')))
        self.assertNotIn('owner_id', hit)

    def test_invalid_citation_does_not_return_a_partial_response(self):
        self.batch['keywords'][0]['locations'] = [2, 2]
        with self.assertRaisesRegex(SearchError, '^library_unavailable$'):
            search('cedar', api=self.api, provider=self.provider, compact=True)

    def test_empty_library_keeps_compact_version_and_skips_inference(self):
        self.session.listing = []
        result = search('cedar', api=self.api, provider=self.provider, compact=True)
        self.assertEqual(result['version'], 'search-previews-v1')
        self.assertEqual(result['windows'], [])
        self.assertEqual(self.provider.calls, [])
        self.assertEqual(len(self.session.calls), 2)
