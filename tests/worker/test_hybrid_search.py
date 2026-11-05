"""Synthetic candidate/transport checks, not live model or RLS evidence."""
import copy
import hashlib
import threading
import unittest
from unittest.mock import Mock

from tests.worker.test_search import Session, Provider
from services.worker.search import search, SearchError
from services.worker.hybrid_search import fuse
from services.worker.search_startup import SearchStartupProvider
from services.worker.model_availability import ModelServiceError


class KeywordSession(Session):
    def __init__(self):
        super().__init__()
        self.keywords = []
        self.deleted = False

    def __call__(self, method, path, payload):
        if path.endswith('search_published_keywords'):
            self.calls.append((method,path,copy.deepcopy(payload)))
            return copy.deepcopy(self.keywords)
        if self.deleted and path.endswith('open_published_text'):
            return []
        return super().__call__(method,path,payload)

    def note(self, text):
        row = self.rows[0]
        doc = self.docs[row['source_id']][0]
        digest = hashlib.sha256(text.encode()).hexdigest()
        doc.update(body=text,source_sha256=digest,passages=[{'id':'p1','start':0,'end':len(text)}])
        row.update(body=text,source_sha256=digest,passage_id='p1',start_offset=0,end_offset=len(text),similarity=.1)
        self.keywords = copy.deepcopy(self.rows)


class HybridTests(unittest.TestCase):
    def setUp(self):
        self.api, self.provider = KeywordSession(), Provider()

    def run_search(self, query='cedar'):
        return search(query,api=self.api,provider=self.provider,hybrid=True)

    def test_low_cosine_exact_word_survives_with_exact_citation(self):
        self.api.note('Archive requests belong in the Cedar queue.')
        result = self.run_search()
        self.assertEqual(len(result['windows']),1)
        self.assertEqual(result['windows'][0]['text'],self.api.rows[0]['body'])
        self.assertEqual(result['windows'][0]['similarity'],.1)
        self.assertEqual(len(self.provider.calls),1)
        self.assertEqual(self.api.calls[3][2]['p_text'],'cedar')
        self.assertNotIn('owner',self.api.calls[3][2])

    def test_mechanism_is_not_bound_to_a_specific_word_or_file(self):
        self.api.note('Orchard backups last fourteen days.')
        self.assertEqual(len(self.run_search('Orchard')['windows']),1)

    def test_no_keyword_hit_preserves_semantic_relevance_gate(self):
        self.api.rows[0]['similarity']=.23
        self.assertEqual(self.run_search()['windows'],[])
        self.api.rows[0]['similarity']=.5
        self.assertEqual(len(self.run_search()['windows']),1)

    def test_duplicate_passage_has_one_source_read(self):
        self.api.note('A Cedar queue note.')
        self.api.rows[0]['similarity']=.7
        self.api.keywords=copy.deepcopy(self.api.rows)
        self.assertEqual(len(self.run_search()['windows']),1)
        self.assertEqual(sum(c[1].endswith('open_published_text') for c in self.api.calls),1)

    def test_invalid_keyword_identity_is_rejected_before_source_reads(self):
        self.api.note('A Cedar queue note.')
        self.api.keywords[0]['model_revision']='wrong'
        with self.assertRaisesRegex(SearchError,'^library_unavailable$'):self.run_search()
        self.assertFalse(any(c[1].endswith('open_published_text') for c in self.api.calls))

    def test_keyword_candidate_disappearing_before_open_is_omitted(self):
        self.api.note('A Cedar queue note.')
        self.api.deleted=True
        self.assertEqual(self.run_search()['windows'],[])

    def test_empty_library_never_starts_service_or_embeds(self):
        self.api.listing=[]
        prepare=Mock()
        wrapped=SearchStartupProvider(self.provider,prepare)
        self.assertEqual(search('cedar',api=self.api,provider=wrapped,hybrid=True)['windows'],[])
        prepare.assert_not_called()
        self.assertFalse(self.provider.calls)

    def test_cache_hit_never_starts_service_or_embeds(self):
        prepare=Mock()
        cache=Mock();cache.get.return_value=[1.]+[0.]*511
        wrapped=SearchStartupProvider(self.provider,prepare)
        search('cedar',api=self.api,provider=wrapped,hybrid=True,query_cache=cache)
        prepare.assert_not_called()
        self.assertFalse(self.provider.calls)

    def test_fusion_is_deterministic_bounded_and_rejects_conflicts(self):
        a=self.api.rows[0]
        b=dict(a,passage_id='second')
        self.assertEqual(fuse([a,b],[b],2),[b,a])
        self.assertEqual(fuse([a],[a],1),[a])
        with self.assertRaises(ValueError):fuse([a],[dict(a,body='different')],2)
        with self.assertRaises(ValueError):fuse([a]*51,[b]*50,20)


class SearchStartupTests(unittest.TestCase):
    def test_ready_precedes_one_inference_and_no_retry_after_failure(self):
        events=[]
        provider=Mock(calls=0)
        provider.infer.side_effect=lambda *a,**kw:events.append('embed') or {'ok':True}
        wrapped=SearchStartupProvider(provider,lambda cancel:events.append('ready'))
        self.assertEqual(wrapped.infer({},cancel=threading.Event()),{'ok':True})
        self.assertEqual(events,['ready','embed'])
        provider.infer.side_effect=RuntimeError('model failure')
        with self.assertRaises(RuntimeError):wrapped.infer({},cancel=threading.Event())
        self.assertEqual(provider.infer.call_count,2)

    def test_startup_failure_does_not_send_embedding(self):
        for code,reason in [('cloud_startup_deadline_exceeded','model_deadline'),
                            ('cloud_startup_http_403','model_access_denied')]:
            provider=Mock(calls=0)
            prepare=Mock(side_effect=RuntimeError(code))
            with self.assertRaises(ModelServiceError) as caught:
                SearchStartupProvider(provider,prepare).infer({},cancel=threading.Event())
            self.assertEqual(caught.exception.reason,reason)
            provider.infer.assert_not_called()
            self.assertEqual(prepare.call_count,1)

    def test_cancel_and_exhausted_budget_never_start_inference(self):
        provider,prepare=Mock(calls=3),Mock()
        wrapped=SearchStartupProvider(provider,prepare)
        with self.assertRaises(ModelServiceError):wrapped.infer({},cancel=threading.Event())
        prepare.assert_not_called();provider.infer.assert_not_called()
        provider.calls=0
        cancel=threading.Event();cancel.set()
        with self.assertRaises(Exception):wrapped.infer({},cancel=cancel)
        prepare.assert_not_called()
        cancel.clear();prepare.side_effect=lambda event:event.set()
        with self.assertRaises(Exception):wrapped.infer({},cancel=cancel)
        provider.infer.assert_not_called()


if __name__=='__main__':unittest.main()
