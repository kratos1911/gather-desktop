"""Injected provider/HTTP fixtures, not live semantic or Auth evidence."""
import copy
import hashlib
import threading
import unittest

from services.inference.runtime import MODEL, REVISION, DIMENSIONS, QUERY_TEMPLATE
from services.worker.search import SearchError, search

OWNER = '00000000-0000-0000-0000-000000000001'


class Provider:
    def __init__(self):
        self.calls, self.counted = [], []
        self.result = dict(model=MODEL, revision=REVISION, dimensions=DIMENSIONS,
                           data=[{'index': 0, 'embedding': [1.] + [0.] * 511}])
        self.tokens = 32

    def count_tokens(self, text):
        self.counted.append(text)
        return self.tokens

    def infer(self, request, *, cancel):
        self.calls.append(copy.deepcopy(request))
        return copy.deepcopy(self.result)


class Session:
    def __init__(self, count=1):
        self.calls, self.rows, self.docs = [], [], {}
        for i in range(count):
            sid = f'00000000-0000-0000-0000-{i+10:012d}'
            vid = f'00000000-0000-0000-0000-{i+100:012d}'
            text = '\ufefffirst\r\nsecond 🌟\nlast'
            sha = hashlib.sha256(text.encode()).hexdigest()
            passages = [dict(id='p1', start=0, end=8), dict(id='p2', start=8, end=17),
                        dict(id='p3', start=17, end=len(text))]
            common = dict(source_id=sid, version_id=vid, source_sha256=sha,
                          model_id=MODEL, model_revision=REVISION, dimensions=DIMENSIONS,
                          title='Synthetic text')
            self.docs[sid] = [dict(common, body=text, passages=passages)]
            self.rows.append(dict(common, passage_id='p2', start_offset=8, end_offset=17,
                                  body=text[8:17], similarity=1 - i * .01))
        self.listing = [dict(source_id=sid,title='Synthetic text',kind='file',
            created_at='2026-10-26T01:00:00.000001Z',published_version_id=docs[0]['version_id'],
            processing_version_id=docs[0]['version_id'],job_id=docs[0]['version_id'],state='ready',attempts=1,error_code=None)
            for sid,docs in sorted(self.docs.items(),reverse=True)]

    def __call__(self, method, path, payload):
        self.calls.append((method, path, copy.deepcopy(payload)))
        if path == '/auth/v1/user':
            return {'id': OWNER}
        if path.endswith('list_library_sources'):
            return copy.deepcopy(self.listing[:payload['p_limit']+1])
        if path.endswith('search_published_text'):
            return copy.deepcopy(self.rows)
        return copy.deepcopy(self.docs[payload['p_source']])


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.api, self.provider = Session(), Provider()

    def run_search(self, **kwargs):
        return search('find stars', api=self.api, provider=self.provider, **kwargs)

    def test_query_template_once_and_exact_cited_context(self):
        result = self.run_search()
        window = result['windows'][0]
        doc = next(iter(self.api.docs.values()))[0]
        self.assertEqual(window['text'], doc['body'])
        self.assertEqual(window['source_sha256'], doc['source_sha256'])
        self.assertEqual((window['start'], window['end']), (0, len(doc['body'])))
        self.assertEqual(self.provider.counted, [QUERY_TEMPLATE.format(text='find stars')])
        self.assertEqual(self.provider.calls, [{'role': 'query', 'texts': ['find stars']}])
        self.assertEqual(self.api.calls[0][1], '/auth/v1/user')
        self.assertEqual(self.api.calls[1][1],'/rest/v1/rpc/list_library_sources')
        for call in self.api.calls[1:]: self.assertNotIn('owner',call[2])

    def test_invalid_queries_do_no_io(self):
        for query in ('', ' ', 'a' * 8193, '\ud800', None):
            with self.subTest(query_type=type(query)), self.assertRaisesRegex(SearchError, '^invalid_query$'):
                search(query, api=self.api, provider=self.provider)
        for limit in (0, 101, True, 1.5):
            with self.assertRaisesRegex(SearchError, '^invalid_query$'):
                self.run_search(limit=limit)
        self.assertEqual(self.api.calls, [])
        self.assertEqual(self.provider.calls, [])

    def test_token_preflight_before_inference(self):
        self.provider.tokens = 2049
        with self.assertRaises(SearchError):
            self.run_search()
        self.assertEqual(self.provider.calls, [])
        self.assertEqual(len(self.api.calls), 2)  # Auth + metadata, no inference.

    def test_auth_failure_prevents_inference_and_redacts(self):
        def denied(*args):
            raise RuntimeError('SECRET token body')
        self.api = denied
        with self.assertRaisesRegex(SearchError, '^session_unavailable$'):
            self.run_search()
        self.assertEqual(self.provider.calls, [])

    def test_model_and_library_failures_are_distinguishable_and_not_retried(self):
        self.provider.infer = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError('private model details'))
        with self.assertRaisesRegex(SearchError, '^model_unavailable$'):
            self.run_search()
        self.assertEqual(self.api.calls[0][1],'/auth/v1/user')
        self.setUp()
        session_api = self.api
        calls=[]
        def rejected(method,path,payload):
            calls.append((method,path,payload))
            if path.endswith('search_published_text'):
                raise RuntimeError('private database detail')
            return session_api(method,path,payload)
        self.api = rejected
        with self.assertRaisesRegex(SearchError,'^library_unavailable$'):
            self.run_search()
        self.assertEqual([call[1] for call in calls],['/auth/v1/user','/rest/v1/rpc/list_library_sources','/rest/v1/rpc/search_published_text'])

    def test_known_model_reason_is_preserved_but_unknown_errors_stay_generic(self):
        from services.worker.model_availability import MODEL_HTTP, ModelServiceError
        for reason in MODEL_HTTP:
            with self.subTest(reason=reason):
                self.setUp()
                def fail(*args,**kwargs):
                    raise ModelServiceError('service_unavailable',reason)
                self.provider.infer=fail
                with self.assertRaisesRegex(SearchError,'^'+reason+'$'): self.run_search()

    def test_bad_embeddings_never_reach_search(self):
        mutations = [dict(revision='wrong'), dict(model='wrong'), dict(dimensions=256),
                     dict(data=[])]
        for vector in ([0]*512, [2]+[0]*511, [float('nan')]+[0]*511, [1]*256):
            mutations.append(dict(data=[dict(index=0, embedding=vector)]))
        for change in mutations:
            with self.subTest(change_keys=list(change)):
                self.setUp()
                self.provider.result.update(change)
                with self.assertRaises(SearchError):
                    self.run_search()
                self.assertEqual([call[1] for call in self.api.calls],['/auth/v1/user','/rest/v1/rpc/list_library_sources'])

    def test_provider_error_not_retried(self):
        def failed(*args, **kwargs):
            self.provider.calls.append('attempt')
            raise RuntimeError('private document')
        self.provider.infer = failed
        with self.assertRaisesRegex(SearchError, '^model_unavailable$'):
            self.run_search()
        self.assertEqual(self.provider.calls, ['attempt'])

    def test_empty_search_does_not_fetch_snapshots(self):
        self.api.rows = []
        self.assertEqual(self.run_search()['windows'], [])
        self.assertEqual(len(self.api.calls), 3)  # Published data exists, but ranker found no hits.

    def test_empty_or_unpublished_library_skips_tokenizer_and_model(self):
        for count in (0,1):
            self.api = Session(count)
            for row in self.api.listing:
                row.update(published_version_id=None,state='queued')
            result = self.run_search()
            self.assertEqual(result['windows'],[])
            self.assertEqual(result['utf8_bytes'],0)
            self.assertEqual(self.provider.calls,[])
            self.assertEqual(self.provider.counted,[])
            self.assertEqual([call[1] for call in self.api.calls],['/auth/v1/user','/rest/v1/rpc/list_library_sources'])

    def test_unknown_or_invalid_metadata_is_not_treated_as_an_empty_library(self):
        self.api.listing[0]['private_original']='must not be exposed'
        with self.assertRaisesRegex(SearchError,'^library_unavailable$'): self.run_search()
        self.assertEqual(self.provider.calls,[])
        self.setUp()
        session = self.api
        def unavailable(method,path,payload):
            if path.endswith('list_library_sources'): raise RuntimeError('private database details')
            return session(method,path,payload)
        self.api = unavailable
        with self.assertRaisesRegex(SearchError,'^library_unavailable$'): self.run_search()
        self.assertEqual(self.provider.calls,[])

    def test_incomplete_first_page_does_not_hide_a_later_published_source(self):
        self.api = Session(22)
        for row in self.api.listing[:-1]: row.update(published_version_id=None,state='queued')
        self.api.rows = self.api.rows[:1]  # This publication is beyond the first metadata page.
        self.assertEqual(len(self.run_search()['windows']),1)
        self.assertEqual(len(self.provider.calls),1)

    def test_reader_race_drops_stale_without_redirect_or_retry(self):
        for _reason in ('deleted', 'replaced'):
            self.setUp()
            self.api.docs[self.api.rows[0]['source_id']] = []
            result = self.run_search()
            self.assertEqual(result['windows'], [])
            self.assertEqual(result['omitted_sources'][0]['reason'], 'no_longer_available')
            self.assertEqual(len(self.api.calls), 4)

    def test_reader_integrity_and_identity_fail_closed(self):
        for change in (dict(version_id=OWNER), dict(source_id=OWNER), dict(source_sha256='0'*64),
                       dict(model_revision='wrong'), dict(body='changed'), dict(passages=[])):
            self.setUp()
            next(iter(self.api.docs.values()))[0].update(change)
            with self.assertRaisesRegex(SearchError, '^library_unavailable$'):
                self.run_search()

    def test_candidate_corruption_is_rejected(self):
        for change in (dict(similarity=float('nan')), dict(model_id='wrong'), dict(start_offset=-1),
                       dict(body='changed'), dict(passage_id='missing'), dict(source_sha256='0'*64)):
            self.setUp()
            self.api.rows[0].update(change)
            with self.assertRaisesRegex(SearchError,'^library_unavailable$'):
                self.run_search()
        self.setUp()
        self.api.rows *= 2
        with self.assertRaisesRegex(SearchError,'^library_unavailable$'):
            self.run_search()

    def test_bounded_fetches_and_all_candidate_validation(self):
        self.api = Session(7)
        result = self.run_search()
        self.assertEqual(len(result['windows']), 5)
        self.assertEqual(len(result['omitted_sources']), 2)
        self.assertEqual(len(self.api.calls), 8)  # Auth + metadata + rank + five reads.
        self.api.rows[-1]['model_revision'] = 'wrong'
        with self.assertRaises(SearchError):
            self.run_search()

    def test_cancel_before_and_during_inference(self):
        cancel = threading.Event()
        cancel.set()
        with self.assertRaisesRegex(SearchError, '^cancelled$'):
            self.run_search(cancel=cancel)
        self.assertEqual(self.api.calls, [])
        cancel.clear()
        original = self.provider.infer
        def cancelled(*args, **kwargs):
            cancel.set()
            return original(*args, **kwargs)
        self.provider.infer = cancelled
        with self.assertRaisesRegex(SearchError, '^cancelled$'):
            self.run_search(cancel=cancel)
        self.assertEqual(len(self.api.calls), 2)

    def test_seed_rank_retains_original_candidate_position(self):
        self.api = Session(2)
        first = self.api.rows[0]
        doc = self.api.docs[first['source_id']][0]
        extra = dict(first, passage_id='p1', start_offset=0, end_offset=8,
                     body=doc['body'][:8], similarity=.995)
        self.api.rows.insert(1, extra)
        self.assertEqual([w['seed_rank'] for w in self.run_search()['windows']], [1, 3])
        self.api.docs[first['source_id']] = []
        self.assertEqual(self.run_search()['windows'][0]['seed_rank'], 3)

    def test_cancellation_during_read_does_not_return_cached_text(self):
        cancel = threading.Event()
        session = self.api
        def interrupted(method, path, payload):
            result = session(method, path, payload)
            if path.endswith('open_published_text'):
                cancel.set()
            return result
        self.api = interrupted
        with self.assertRaisesRegex(SearchError, '^cancelled$'):
            self.run_search(cancel=cancel)


if __name__ == '__main__':
    unittest.main()
