"""Synthetic scheduling/protocol controls. Timings here are not cloud speedups."""
import json
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import Mock, patch

from services.worker.automatic_processing import StartupProvider
from services.worker.database_transport import DatabaseRepository, DatabaseConfig, SLOTS
from services.worker.database_session import acquire_slot
from services.worker.ingestion_repository import RepositoryError
from services.worker.processing_timing import safe_timing
from services.worker.worker_lifecycle import WorkerRun
from tests.worker.test_ingestion import MemoryRepository, SyntheticProvider

CHILD=r'''
import json,struct,sys,time
first=True
while True:
 h=sys.stdin.buffer.read(4)
 if not h:break
 v=json.loads(sys.stdin.buffer.read(struct.unpack('!I',h)[0]))
 if v['args'] and v['args'][0]=='stall':time.sleep(30)
 reply={'sequence':v['sequence'],'result':None,'timing':{'connects':int(first)}}
 first=False
 raw=json.dumps(reply).encode()
 sys.stdout.buffer.write(struct.pack('!I',len(raw))+raw);sys.stdout.buffer.flush()
'''


class PipelineTests(unittest.TestCase):
    def test_background_wait_has_its_own_existing_sixty_second_bound(self):
        from services.inference.runtime import InferenceError
        started=threading.Event()
        cancel=threading.Event()
        def stalled(cancel):
            started.set();cancel.wait(2)
        inner=SyntheticProvider();inner.infer=Mock()
        provider=StartupProvider(inner,stalled,background=True)
        provider.start_prepare(cancel=cancel)
        self.assertTrue(started.wait(1))
        provider._preparation_deadline=time.monotonic()-.01  # Controlled clock edge, no real 60s sleep.
        try:
            with self.assertRaises(InferenceError):provider.infer({},cancel=cancel)
            self.assertEqual(provider.startup_error,'cloud_startup_deadline_exceeded')
            inner.infer.assert_not_called()
        finally:
            cancel.set();provider.close_preparation()

    def test_preparation_overlaps_parse_and_staging_without_early_embedding(self):
        repo,inner=MemoryRepository(),SyntheticProvider()
        started,release=threading.Event(),threading.Event()
        def prepare(cancel):
            started.set()
            while not release.wait(.01):
                if cancel.is_set():return
        provider=StartupProvider(inner,prepare,background=True)
        from services.worker.ingestion import parse
        def parser(*args,**kwargs):
            self.assertTrue(started.wait(1))
            self.assertFalse(release.is_set())
            return parse(*args,**kwargs)
        original=repo.call
        def store(name,*args):
            if name=='stage_text':release.set()
            return original(name,*args)
        repo.call=store
        with patch('services.worker.ingestion.parse',side_effect=parser):
            result=WorkerRun(repo,provider,record_timings=True).run()['outcomes'][0]
        self.assertEqual(result['state'],'ready')
        self.assertTrue(result['timing']['early_prepare'])
        self.assertGreaterEqual(result['timing']['preparation_ms'],0)
        self.assertFalse(provider._thread.is_alive())
        self.assertEqual(set(result['timing']['stages_ms'])-set(
            ('claim','renew_lease','validate_manifest','read_original','parse_original','chunk_original',
             'stage_text','read_completed_passages','embed_passage','stage_vectors','publish')),set())

    def test_parse_failure_cancels_preparation_and_never_embeds(self):
        started,ended=threading.Event(),threading.Event()
        def prepare(cancel):
            started.set();cancel.wait(2);ended.set()
        inner=SyntheticProvider();inner.infer=Mock()
        provider=StartupProvider(inner,prepare,background=True)
        def invalid(*a,**k):
            self.assertTrue(started.wait(1));raise ValueError('synthetic invalid original')
        with patch('services.worker.ingestion.parse',side_effect=invalid):
            result=WorkerRun(MemoryRepository(),provider).run()['outcomes'][0]
        self.assertEqual(result['error_code'],'invalid_input')
        self.assertTrue(ended.is_set())
        self.assertFalse(provider._thread.is_alive())
        inner.infer.assert_not_called()

    def test_startup_failure_is_visible_without_inference_replay(self):
        inner=SyntheticProvider();inner.infer=Mock()
        def unavailable(cancel):raise RuntimeError('private provider details')
        provider=StartupProvider(inner,unavailable,background=True)
        result=WorkerRun(MemoryRepository(),provider,record_timings=True).run()['outcomes'][0]
        self.assertEqual(result['state'],'queued')
        self.assertEqual(provider.startup_error,'startup_unavailable')
        inner.infer.assert_not_called()
        self.assertFalse(provider._thread.is_alive())

    def test_timing_log_rejects_content_unknown_fields_and_nonfinite_values(self):
        from services.worker.cloud_library import processing_log
        for measurements in ({'total_ms':1,'stages_ms':{},'document':'PRIVATE'},
            {'total_ms':float('nan'),'stages_ms':{}},
            {'total_ms':1,'stages_ms':{'PRIVATE':2}},
            {'total_ms':1,'stages_ms':{},'database':{'password':'PRIVATE'}}):
            self.assertIsNone(safe_timing(measurements))
            self.assertNotIn('PRIVATE',processing_log({'outcomes':[{'state':'ready','timing':measurements}]},1))
        valid={'total_ms':3,'stages_ms':{'claim':2},'preparation_ms':10,'early_prepare':True}
        self.assertEqual(safe_timing(valid),valid)  # Overlap is not added to wall time.


class SessionProtocolTests(unittest.TestCase):
    def config(self,role='gather_worker'):
        return DatabaseConfig('127.0.0.1',5432,role,'synthetic-secret',test_loopback=True)

    def fixture_processes(self):
        original=subprocess.Popen
        self.processes=[]
        def start(*args,**kwargs):
            self.assertNotIn('synthetic-secret',repr(args))
            self.assertNotIn('PGPASSWORD',kwargs['env'])
            process=original([sys.executable,'-I','-B','-u','-c',CHILD],**kwargs)
            self.processes.append(process)
            return process
        return patch('services.worker.database_session.subprocess.Popen',side_effect=start)

    def test_reuses_helper_with_stdin_only_credentials_and_reaps_at_job_end(self):
        repository=DatabaseRepository(self.config(),reuse_worker=True)
        with self.fixture_processes():
            with repository.job_scope():
                self.assertIsNone(repository.call('claim_text_job'))
                self.assertIsNone(repository.call('renew_text_job','job','token'))
            self.assertEqual(len(self.processes),1)
            self.assertEqual(repository.last_job_metrics['helpers_started'],1)
            self.assertEqual(repository.last_job_metrics['connects'],1)
            self.assertEqual(repository.last_job_metrics['operations'],2)
        self.assertTrue(all(p.poll() is not None for p in self.processes))

    def test_deadline_kills_helper_without_replaying_the_uncertain_call(self):
        repository=DatabaseRepository(self.config(),reuse_worker=True)
        with self.fixture_processes():
            with repository.job_scope():
                repository.call('claim_text_job')
                repository.operation_timeout=.15  # Fixture only; production constructor still rejects it.
                began=time.monotonic()
                with self.assertRaisesRegex(RepositoryError,'temporarily_unavailable'):
                    repository.call('renew_text_job','stall','token')
                self.assertLess(time.monotonic()-began,3)
                self.assertIsNotNone(self.processes[0].poll())
                repository.operation_timeout=5
                repository.call('claim_text_job')  # Different, explicit operation, not an automatic replay.
            self.assertEqual(len(self.processes),2)
            self.assertEqual(repository.last_job_metrics['operations'],3)

    def test_idle_eviction_keeps_two_physical_helper_slots_and_active_work_is_not_evicted(self):
        repository=DatabaseRepository(self.config(),reuse_worker=True)
        with self.fixture_processes(),repository.job_scope():
            repository.call('claim_text_job')
            helper=next(iter(repository._scope.helpers.values()))
            self.assertTrue(SLOTS.acquire(blocking=False))
            try:
                helper.operation.acquire()
                try:self.assertFalse(acquire_slot())
                finally:helper.operation.release()
                self.assertTrue(acquire_slot())  # Evicts the idle cached helper.
                SLOTS.release()
                self.assertIsNotNone(self.processes[0].poll())
            finally:SLOTS.release()

    def test_admission_reuse_and_foreign_operations_are_denied(self):
        with self.assertRaisesRegex(ValueError,'worker_reuse_only'):
            DatabaseRepository(self.config('gather_admission'),
                owner='00000000-0000-0000-0000-000000000001',reuse_worker=True)
        repository=DatabaseRepository(self.config(),reuse_worker=True)
        with repository.job_scope(),patch('services.worker.database_session.subprocess.Popen') as start:
            with self.assertRaises(ValueError):repository.call('submit_text',*([None]*10))
            start.assert_not_called()


if __name__=='__main__':unittest.main()
