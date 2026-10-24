"""Synthetic workflow controls; real SQL lease expiry has separate evidence."""
import threading
import unittest
from unittest.mock import Mock

from services.worker.ingestion import run_once
from services.worker.worker_lifecycle import WorkerRun
from tests.worker.test_ingestion import MemoryRepository, SyntheticProvider


class LifecycleTests(unittest.TestCase):
    def test_stop_before_claim_has_no_side_effects(self):
        repo = MemoryRepository()
        run = WorkerRun(repo,SyntheticProvider())
        run.stop()
        self.assertEqual(run.run(),{'stopped':True,'outcomes':[]})
        self.assertEqual(repo.calls,[])

    def test_stop_after_claim_leaves_lease_for_recovery(self):
        repo, event = MemoryRepository(), threading.Event()
        original = repo.call
        def call(name,*args):
            value = original(name,*args)
            if name == 'claim_text_job': event.set()
            return value
        repo.call = call
        self.assertEqual(run_once(repo,SyntheticProvider(),cancel=event)['state'],'abandoned')
        self.assertEqual([n for n,_ in repo.calls],['claim_text_job'])

    def test_stop_during_inference_cancels_and_never_stages_or_publishes(self):
        repo, provider = MemoryRepository(), SyntheticProvider()
        run = WorkerRun(repo,provider)
        entered = threading.Event()
        def infer(request,*,cancel):
            entered.set()
            self.assertTrue(cancel.wait(2))
            return SyntheticProvider().infer(request,cancel=cancel)
        provider.infer = infer
        results = []
        thread = threading.Thread(target=lambda:results.append(run.run()))
        thread.start()
        self.assertTrue(entered.wait(1))
        with self.assertRaisesRegex(RuntimeError,'worker_busy'): run.run()
        run.stop()
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(results[0]['outcomes'][0]['state'],'abandoned')
        names = [n for n,_ in repo.calls]
        self.assertNotIn('stage_vectors',names)
        self.assertNotIn('publish_text',names)
        self.assertNotIn('fail_text_job',names)

    def test_stop_before_publish_never_activates_version(self):
        repo, event = MemoryRepository(), threading.Event()
        original = repo.call
        def call(name,*args):
            value = original(name,*args)
            if name == 'stage_vectors': event.set()
            return value
        repo.call = call
        self.assertEqual(run_once(repo,SyntheticProvider(),cancel=event)['state'],'abandoned')
        self.assertNotIn('publish_text',[n for n,_ in repo.calls])

    def test_recovery_reuses_saved_vectors(self):
        repo, provider = MemoryRepository(), SyntheticProvider()
        original = repo.call
        completed = []
        event = threading.Event()
        def call(name,*args):
            value = original(name,*args)
            if name == 'completed_passages': return list(completed)
            if name == 'stage_vectors':
                completed.extend(row['id'] for row in args[-1])
                event.set()
            return value
        repo.call = call
        self.assertEqual(run_once(repo,provider,cancel=event)['state'],'abandoned')
        first = len(completed)
        self.assertEqual(first,1)
        provider.infer = Mock(wraps=provider.infer)
        # Synthetic renewed lease; SQL expiry/fencing is covered separately.
        self.assertEqual(run_once(repo,provider)['state'],'ready')
        self.assertEqual(provider.infer.call_count,len(completed)-first)
        self.assertEqual(len(set(completed)),len(completed))

    def test_bounded_claims_and_no_automatic_failure_retry(self):
        repo = MemoryRepository()
        run = WorkerRun(repo,SyntheticProvider())
        self.assertEqual(len(run.run(max_jobs=2)['outcomes']),2)
        repo.call = Mock(side_effect=RuntimeError('secret database details'))
        self.assertEqual(run.run(max_jobs=3)['outcomes'],[{'state':'unavailable'}])
        self.assertEqual(repo.call.call_count,1)
        for value in (0,4,True):
            with self.assertRaises(ValueError): run.run(max_jobs=value)
