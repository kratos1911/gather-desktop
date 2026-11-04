"""Synthetic Redis/crypto and coordinator checks; no live Redis or model calls."""
import copy
import base64
import json
import threading
import unittest
from unittest.mock import patch, Mock

from services.worker.query_cache import QueryCache, TTL_SECONDS, from_environment
from services.worker.service_transport import TransportError
from services.worker.search import SearchError, search
from tests.worker.test_search import Session, Provider, OWNER

OTHER = '00000000-0000-0000-0000-000000000002'
QUERY = 'Private synthetic query about a Cedar queue'
VECTOR = [1.] + [0.]*511


class Redis:
    def __init__(self):
        self.data, self.calls, self.failure = {}, [], False

    def __call__(self, endpoint, path, headers, command, **options):
        self.calls.append(copy.deepcopy(command))
        if self.failure:
            raise RuntimeError('private upstream details and token')
        if command[0] == 'GET':
            return {'result': self.data.get(command[1])}
        if command[0] != 'SET' or command[3:] != ['EX',TTL_SECONDS]:
            raise AssertionError('unexpected command')
        self.data[command[1]] = command[2]
        return {'result':'OK'}


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.redis, self.events, self.now = Redis(), [], [1000]
        self.cache = QueryCache('https://gather-fixture.upstash.io','synthetic-token',b'k'*32,
            _transport=self.redis,_clock=lambda:self.now[0],_monotonic=lambda:self.now[0],
            record=self.events.append)

    def test_encrypted_roundtrip_no_plaintext_query_owner_or_vector_in_commands(self):
        self.cache.put(OWNER,QUERY,VECTOR)
        self.assertEqual(self.cache.get(OWNER,QUERY), VECTOR)
        wire = json.dumps(self.redis.calls)
        self.assertNotIn(QUERY,wire)
        self.assertNotIn(OWNER,wire)
        self.assertNotIn('vector',wire)
        self.assertEqual(self.events,['stored','hit'])
        self.assertEqual(self.redis.calls[0][-2:],['EX',600])

    def test_owner_and_exact_query_isolation(self):
        self.cache.put(OWNER,QUERY,VECTOR)
        self.assertIsNone(self.cache.get(OTHER,QUERY))
        self.assertIsNone(self.cache.get(OWNER,QUERY+' changed'))
        source = next(iter(self.redis.data.values()))
        # Copying a ciphertext to another user's valid key fails its AAD check.
        self.redis.data[self.cache._key(OTHER,QUERY)] = source
        self.assertIsNone(self.cache.get(OTHER,QUERY))

    def test_model_revision_dimensions_and_prompt_change_miss(self):
        self.cache.put(OWNER,QUERY,VECTOR)
        for field,value in [('MODEL','different'),('REVISION','different'),
                            ('DIMENSIONS',256),('QUERY_TEMPLATE','different {text}')]:
            with patch('services.worker.query_cache.'+field,value):
                self.assertIsNone(self.cache.get(OWNER,QUERY))

    def test_expiry_and_tampering_are_misses_and_valid_write_repairs(self):
        self.cache.put(OWNER,QUERY,VECTOR)
        self.now[0] += TTL_SECONDS
        self.assertIsNone(self.cache.get(OWNER,QUERY))
        self.cache.put(OWNER,QUERY,VECTOR)
        self.assertEqual(self.cache.get(OWNER,QUERY),VECTOR)
        key=next(iter(self.redis.data))
        self.redis.data[key] = 'A'*64
        self.assertIsNone(self.cache.get(OWNER,QUERY))
        self.cache.put(OWNER,QUERY,VECTOR)
        self.assertEqual(self.cache.get(OWNER,QUERY),VECTOR)

    def test_invalid_outputs_never_cached(self):
        for vector in ([0.]*512,[1.]*256,[float('nan')]+[0.]*511,[True]+[0.]*511):
            self.now[0] += 31
            self.cache.put(OWNER,QUERY,vector)
        self.assertFalse(self.redis.calls)

    def test_network_failure_has_backoff_and_no_automatic_retry(self):
        self.redis.failure=True
        self.assertIsNone(self.cache.get(OWNER,QUERY))
        self.cache.put(OWNER,QUERY,VECTOR)
        self.assertIsNone(self.cache.get(OWNER,QUERY))
        self.assertEqual(len(self.redis.calls),1)
        self.now[0] += 31
        self.redis.failure=False
        self.assertIsNone(self.cache.get(OWNER,QUERY))
        self.assertEqual(len(self.redis.calls),2)

    def test_bounded_transport_deadline_and_allowlisted_error_diagnostics(self):
        def timeout(*args,**kwargs):
            self.assertEqual(kwargs['timeout'],1)
            raise TransportError('timeout')
        self.cache._send=timeout
        self.assertIsNone(self.cache.get(OWNER,QUERY))
        self.assertEqual(self.events,['error','transport_timeout'])
        self.events.clear();self.now[0]+=31
        def private(*args,**kwargs):raise TransportError('private secret body')
        self.cache._send=private
        self.assertIsNone(self.cache.get(OWNER,QUERY))
        self.assertEqual(self.events,['error'])

    def test_default_off_and_untrusted_endpoint_rejected(self):
        self.assertIsNone(from_environment({}))
        for url in ('http://fixture.upstash.io','https://fixture.upstash.io.evil.test',
                    'https://127.0.0.1','https://fixture.upstash.io/path',
                    'https://user:secret@fixture.upstash.io','https://fixture.upstash.io:444'):
            with self.subTest(url=url), self.assertRaises(Exception):
                QueryCache(url,'synthetic',b'k'*32,_transport=self.redis)
        with self.assertRaises(ValueError):
            from_environment({'GATHER_QUERY_CACHE':'unknown'})

    def test_cancellation_does_no_cache_io(self):
        cancelled=threading.Event(); cancelled.set()
        self.assertIsNone(self.cache.get(OWNER,QUERY,cancel=cancelled))
        self.cache.put(OWNER,QUERY,VECTOR,cancel=cancelled)
        self.assertFalse(self.redis.calls)

    def test_enabled_configuration_requires_both_mounted_secrets(self):
        values={'/secrets/gather_query_cache/key':base64.b64encode(b'k'*32).decode(),
                '/secrets/gather_upstash/token':'synthetic-token'}
        def file(path):
            value=Mock()
            value.is_symlink.return_value=False
            value.is_file.return_value=True
            value.stat.return_value.st_size=len(values[path])
            value.read_text.return_value=values[path]
            return value
        with patch('services.worker.query_cache.Path',side_effect=file):
            cache=from_environment({'GATHER_QUERY_CACHE':'1',
                'GATHER_UPSTASH_URL':'https://gather-fixture.upstash.io'})
            self.assertIsInstance(cache,QueryCache)
        with patch('services.worker.query_cache.Path') as path:
            path.return_value.is_symlink.return_value=True
            with self.assertRaises(ValueError):
                from_environment({'GATHER_QUERY_CACHE':'1'})

    def run_search(self, api=None, provider=None, cancel=None):
        return search(QUERY,api=api or self.api,provider=provider or self.provider,
                      query_cache=self.cache,cancel=cancel)

    def test_repeat_skips_model_but_auth_metadata_ranking_and_reads_remain_fresh(self):
        self.api,self.provider=Session(),Provider()
        first=self.run_search();self.api.calls.clear()
        self.assertEqual(self.run_search(),first)
        self.assertEqual(len(self.provider.calls),1)
        self.assertEqual([c[1] for c in self.api.calls],['/auth/v1/user',
            '/rest/v1/rpc/list_library_sources','/rest/v1/rpc/search_published_text',
            '/rest/v1/rpc/open_published_text'])

    def test_auth_failure_prevents_even_a_cache_hit(self):
        self.cache.put(OWNER,QUERY,VECTOR);self.redis.calls.clear()
        self.api,self.provider=Session(),Provider()
        def denied(*_):raise RuntimeError('private auth detail')
        with self.assertRaisesRegex(SearchError,'^session_unavailable$'):
            self.run_search(api=denied)
        self.assertFalse(self.redis.calls)
        self.assertFalse(self.provider.calls)

    def test_deletion_and_replacement_checked_on_hit_without_stale_results(self):
        self.api,self.provider=Session(),Provider()
        self.run_search()
        sid=self.api.rows[0]['source_id']
        self.api.docs[sid]=[]
        self.assertEqual(self.run_search()['windows'],[])
        self.assertEqual(len(self.provider.calls),1)
        self.api.listing=[];self.redis.calls.clear()
        self.assertEqual(self.run_search()['windows'],[])
        self.assertFalse(self.redis.calls)

    def test_cache_failure_falls_back_once_and_preserves_cancellation(self):
        self.api,self.provider=Session(),Provider();self.redis.failure=True
        self.assertEqual(len(self.run_search()['windows']),1)
        self.assertEqual(len(self.provider.calls),1)
        self.assertEqual(len(self.redis.calls),1)
        cancel=threading.Event()
        self.now[0]+=31
        def cancelled(*args,**kwargs):cancel.set();raise RuntimeError('cancelled')
        self.cache._send=cancelled
        with self.assertRaisesRegex(SearchError,'^cancelled$'):
            self.run_search(cancel=cancel)
        self.assertEqual(len(self.provider.calls),1)

    def test_hit_needs_no_new_model_budget_but_miss_preserves_exhaustion(self):
        from services.worker.model_availability import ModelServiceError
        self.api,self.provider=Session(),Provider()
        self.run_search()
        self.provider.infer=Mock(side_effect=ModelServiceError('service_unavailable','model_budget_exhausted'))
        self.assertEqual(len(self.run_search()['windows']),1)
        self.provider.infer.assert_not_called()
        with self.assertRaisesRegex(SearchError,'^model_budget_exhausted$'):
            search(QUERY+'new',api=self.api,provider=self.provider,query_cache=self.cache)


if __name__ == '__main__':
    unittest.main()
