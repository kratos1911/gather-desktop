"""Coordinator controls with injected fixtures; no semantic inference evidence."""
import hashlib
import threading
import unittest
from unittest.mock import Mock, MagicMock

from services.worker.ingestion import (submit, run_once, Lease, RuntimeProvider,
    MODEL, REVISION, DIMENSIONS, VERSION, PARSER_VERSION)
from services.worker.ingestion_repository import PostgresRepository, RepositoryError
from services.inference.runtime import InferenceError


class SyntheticProvider:
    """Protocol fixture uses expected metadata; vectors have no semantic meaning."""
    def count_tokens(self, text):
        return len(text)

    def infer(self, request, *, cancel):
        if cancel.is_set():
            raise InferenceError('cancelled')
        return dict(model=MODEL, revision=REVISION, dimensions=DIMENSIONS,
                    data=[dict(index=0, embedding=[1.0]+[0.0]*(DIMENSIONS-1))])


class MemoryRepository:
    def __init__(self):
        self.raw = b'Synthetic coordinator text. ' * 30
        self.job = dict(id='job',lease_token='token',version_id='version',
            media_type='text/plain',input_bytes=len(self.raw),content_sha256=hashlib.sha256(self.raw).hexdigest(),
            parser_version=PARSER_VERSION,chunker_version=VERSION,model_id=MODEL,model_revision=REVISION,dimensions=DIMENSIONS)
        self.calls = []
        self.stale = False

    def call(self, name, *args):
        self.calls.append((name,args))
        if self.stale and name != 'claim_text_job':
            raise RepositoryError('stale_lease')
        return {'claim_text_job': self.job, 'read_job_original': self.raw.hex(),
                'publish_text': 'version', 'fail_text_job': 'queued', 'completed_passages': []}.get(name)


class IngestionTests(unittest.TestCase):
    def test_staging_failure_has_safe_reason_and_never_embeds_or_publishes(self):
        repo = MemoryRepository()
        original = repo.call
        def fail(name,*args):
            if name=='stage_text':
                raise RepositoryError('temporarily_unavailable',reason='sqlstate_55P03')
            return original(name,*args)
        repo.call = fail
        provider = SyntheticProvider()
        provider.infer = Mock()
        result = run_once(repo,provider)
        self.assertEqual(result['diagnostic'],{'step':'stage_text','reason':'sqlstate_55P03'})
        provider.infer.assert_not_called()
        self.assertNotIn('publish_text',[name for name,args in repo.calls])

    def test_read_failure_preserves_safe_step_and_reason(self):
        repo = MemoryRepository()
        original = repo.call
        def fail(name,*args):
            if name=='read_job_original':
                raise RepositoryError('temporarily_unavailable',reason='operation_deadline_exceeded')
            return original(name,*args)
        repo.call = fail
        result = run_once(repo,SyntheticProvider())
        self.assertEqual(result['state'],'queued')
        self.assertEqual(result['diagnostic'],{'step':'read_original','reason':'operation_deadline_exceeded'})

    def test_lease_failure_keeps_fencing_and_safe_reason(self):
        repo = MemoryRepository()
        original = repo.call
        def fail(name,*args):
            if name=='renew_text_job':
                raise RepositoryError('temporarily_unavailable',reason='sqlstate_57014')
            return original(name,*args)
        repo.call = fail
        result = run_once(repo,SyntheticProvider())
        self.assertEqual(result['state'],'abandoned')
        self.assertEqual(result['diagnostic'],{'step':'renew_lease','reason':'sqlstate_57014'})
    def test_lease_cleanup_uses_bounded_explicit_repository_timeout(self):
        for selected,expected in ((6,6),(16,16),(999,6)):
            repo = MemoryRepository()
            repo.cleanup_wait_seconds = selected
            lease = Lease(repo,repo.job)
            lease.thread = Mock(ident=1)
            lease.__exit__()
            lease.thread.join.assert_called_once_with(expected)

    def test_success_connects_all_steps(self):
        repo = MemoryRepository()
        self.assertEqual(run_once(repo,SyntheticProvider())['state'],'ready')
        names = [n for n,_ in repo.calls]
        self.assertLess(names.index('stage_text'),names.index('stage_vectors'))
        self.assertGreater(names.count('stage_vectors'),1)
        self.assertEqual(names[-1],'publish_text')

    def test_rejects_bad_submissions_before_database(self):
        repo = Mock()
        for original,media in ((b'','text/plain'),(b'x'*65537,'text/plain'),(b'\xff','text/plain'),(b'x','image/png')):
            with self.assertRaises(ValueError):
                submit(repo,request_id='00000000-0000-0000-0000-000000000001',title='fixture',original=original,media=media)
        repo.call.assert_not_called()

    def test_lost_lease_stops_later_batches(self):
        repo, provider = MemoryRepository(), SyntheticProvider()
        original = provider.infer
        def infer(request, *, cancel):
            repo.stale = True
            return original(request,cancel=cancel)
        provider.infer = infer
        self.assertEqual(run_once(repo,provider)['state'],'abandoned')
        self.assertNotIn('stage_vectors',[n for n,_ in repo.calls])
        self.assertNotIn('publish_text',[n for n,_ in repo.calls])

    def test_provider_error_mapping_and_redaction(self):
        for error,code in ((InferenceError('deadline_exceeded'),'timeout'),
                           (InferenceError('model_failed'),'temporarily_unavailable')):
            repo,provider = MemoryRepository(),SyntheticProvider()
            provider.infer = Mock(side_effect=error)
            self.assertEqual(run_once(repo,provider)['error_code'],code)
        repo,provider = MemoryRepository(),SyntheticProvider()
        provider.infer = Mock(return_value={'private':'sensitive text'})
        self.assertEqual(run_once(repo,provider)['error_code'],'invalid_input')
        self.assertNotIn('publish_text',[n for n,_ in repo.calls])

    def test_corrupt_original_and_configuration_fail_before_inference(self):
        for key,value in (('content_sha256','0'*64),('model_revision','wrong')):
            repo,provider = MemoryRepository(),Mock()
            repo.job[key] = value
            self.assertEqual(run_once(repo,provider)['error_code'],'invalid_input')
            provider.infer.assert_not_called()

    def test_job_budget_rejected_before_first_embedding(self):
        repo,provider = MemoryRepository(),SyntheticProvider()
        repo.raw = b'long fixture ' * 1000
        repo.job.update(input_bytes=len(repo.raw),content_sha256=hashlib.sha256(repo.raw).hexdigest())
        provider.infer = Mock()
        self.assertEqual(run_once(repo,provider)['error_code'],'invalid_input')
        provider.infer.assert_not_called()

    def test_background_heartbeat_signals_cancellation(self):
        repo = MemoryRepository()
        lease = Lease(repo,repo.job)
        # Drive one periodic tick without sleeping or changing production limits.
        lease.stopped = Mock()
        lease.stopped.wait.return_value = False
        repo.stale = True
        lease._heartbeat()
        self.assertTrue(lease.cancelled.is_set())

    def test_runtime_bridge_preserves_cancellation_and_limit(self):
        runtime = Mock(request_timeout=15)
        provider = RuntimeProvider(runtime,len)
        cancel = threading.Event()
        provider.infer({'role':'document','texts':['x']},cancel=cancel)
        runtime.infer.assert_called_once_with({'role':'document','texts':['x']},cancel=cancel)
        with self.assertRaises(ValueError):
            RuntimeProvider(Mock(request_timeout=16),len)

    def test_db_adapter_parameterizes_and_closes(self):
        connection = MagicMock(autocommit=False)
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = ('result',)
        repo = PostgresRepository(lambda: connection)
        self.assertEqual(repo.call('read_job_original',"quote'",'token'),'result')
        self.assertEqual(cursor.execute.call_args.args,('select gather_private.read_job_original(%s,%s)',("quote'",'token')))
        connection.commit.assert_called_once()
        connection.close.assert_called_once()
        with self.assertRaises(ValueError):
            repo.call('unsafe;sql')

    def test_db_adapter_rolls_back_and_redacts(self):
        connection = Mock(autocommit=False)
        error = Exception('secret document')
        error.pgcode = '55000'
        connection.cursor.side_effect = error
        with self.assertRaisesRegex(RepositoryError,'^stale_lease$'):
            PostgresRepository(lambda: connection).call('claim_text_job')
        connection.rollback.assert_called_once()
        connection.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
