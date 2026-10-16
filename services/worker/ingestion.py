"""Trusted, bounded ingestion orchestration. No default embedding provider.

submit() is internal admission, run_once() handles one durable claim. Scheduling,
retry/backoff and publication correctness remain in existing PostgreSQL functions.
"""
import base64
import json
import threading
from uuid import UUID

from services.inference.chunking import chunk_document, VERSION, MAX_TOKENS
from services.inference.runtime import MODEL, REVISION, DIMENSIONS, InferenceError
from services.worker.embedding_client import embed_texts, Limits, EmbeddingError
from services.worker.ingestion_repository import RepositoryError
from services.worker.text_processing import process_request, PARSER_VERSION, MAX_SOURCE_BYTES

MAX_JOB_REQUESTS = 16  # Preserve the embedding client's default request budget.
MAX_JOB_TOKENS = MAX_JOB_REQUESTS * MAX_TOKENS


class ProviderFailure(EmbeddingError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class RuntimeProvider:
    """Bridge to an explicitly started Runtime and its pinned tokenizer.

    Does not start/download models. Cloud transport will implement this same
    interface with a hard deadline and cancellation of its active request.
    """
    def __init__(self, runtime, count_tokens):
        if runtime.request_timeout > 15:
            raise ValueError('request_deadline_exceeds_limit')
        self.runtime, self.count_tokens = runtime, count_tokens

    def infer(self, request, *, cancel):
        return self.runtime.infer(request, cancel=cancel)


def parse(raw, media):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_SOURCE_BYTES or media not in ('text/plain','text/markdown'):
        raise ValueError('invalid_input')
    result = process_request(json.dumps(dict(version=1, request_id='ingestion',
        format='txt' if media == 'text/plain' else 'md',
        content_base64=base64.b64encode(raw).decode('ascii'))).encode())
    if result['status'] != 'processed':
        raise ValueError('invalid_input')
    return result['document']


def submit(repository, *, request_id, title, original, media, source_id=None):
    """Repository connection supplies verified auth context; payload has no owner."""
    UUID(request_id)
    if source_id is not None:
        UUID(source_id)
    if not isinstance(title, str) or not title.strip() or len(title) > 500:
        raise ValueError('invalid_input')
    parse(original, media)
    return repository.call('submit_text', request_id, title, original, media,
                           PARSER_VERSION, VERSION, MODEL, REVISION, DIMENSIONS, source_id)


class Lease:
    def __init__(self, repository, job):
        self.repository, self.job = repository, job
        self.cancelled = threading.Event()
        self.stopped = threading.Event()
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._heartbeat, daemon=True)

    def check(self):
        if self.cancelled.is_set():
            raise RepositoryError('stale_lease')

    def renew(self):
        with self.lock:
            self.check()
            try:
                self.repository.call('renew_text_job', self.job['id'], self.job['lease_token'])
            except Exception:
                self.cancelled.set()
                raise RepositoryError('stale_lease') from None

    def _heartbeat(self):
        while not self.stopped.wait(10):
            try:
                self.renew()
            except RepositoryError:
                return

    def __enter__(self):
        self.renew()
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stopped.set()
        self.cancelled.set()
        if self.thread.ident is not None:
            self.thread.join(6)  # Repository operations have a five-second deadline.


def run_once(repository, provider):
    """Provider supplies count_tokens(text), infer(request, cancel=event).

    The tokenizer must match the pinned Qwen revision. An already-started Runtime
    can supply infer; a future cloud adapter must honor the same cancellation and
    request deadlines. Test providers are injected only from tests.
    """
    job = repository.call('claim_text_job')
    if job is None:
        return {'state': 'idle'}
    args = (job['id'], job['lease_token'])
    try:
        with Lease(repository, job) as lease:
            if (job['parser_version'],job['chunker_version'],job['model_id'],job['model_revision'],job['dimensions']) != (
                    PARSER_VERSION,VERSION,MODEL,REVISION,DIMENSIONS):
                raise ValueError('invalid_input')
            raw = bytes.fromhex(repository.call('read_job_original', *args))
            document = parse(raw, job['media_type'])
            if len(raw) != job['input_bytes'] or document['source_sha256'] != job['content_sha256']:
                raise ValueError('invalid_input')

            def count_tokens(text):
                lease.check()
                return provider.count_tokens(text)

            chunks = chunk_document(raw.decode('utf-8'), count_tokens)
            if len(chunks) > MAX_JOB_REQUESTS or sum(c['tokens'] for c in chunks) > MAX_JOB_TOKENS:
                raise ValueError('invalid_input')
            lease.renew()
            repository.call('stage_text', *args, raw, job['media_type'],
                            [{k: c[k] for k in ('id','start','end')} for c in chunks])
            completed = set(repository.call('completed_passages', *args))
            for chunk in chunks:
                if chunk['id'] in completed:
                    continue
                lease.renew()

                def send(body):
                    lease.check()
                    try:
                        result = provider.infer({'role': 'document', 'texts': body['input']}, cancel=lease.cancelled)
                    except InferenceError as error:
                        code = 'timeout' if str(error) == 'deadline_exceeded' else (
                            'invalid_input' if str(error) in ('token_limit','invalid_request','invalid_model_output')
                            else 'temporarily_unavailable')
                        raise ProviderFailure(code) from None
                    lease.check()
                    if not isinstance(result, dict) or (result.get('model'),result.get('revision'),result.get('dimensions')) != (MODEL,REVISION,DIMENSIONS):
                        raise EmbeddingError('Invalid provider identity')
                    return result

                result = embed_texts([chunk['text']], model=MODEL,
                    limits=Limits(DIMENSIONS,MAX_TOKENS,MAX_TOKENS,1,1), count_tokens=count_tokens, send=send)
                lease.renew()
                repository.call('stage_vectors', *args, MODEL, REVISION, DIMENSIONS,
                                [{'id':chunk['id'],'vector':result['vectors'][0]}])
            # Prevent heartbeat racing a successful ready transition.
            with lease.lock:
                lease.check()
                version = repository.call('publish_text', *args)
                lease.stopped.set()
            return {'state':'ready','job_id':job['id'],'version_id':version}
    except Exception as error:
        if isinstance(error, RepositoryError) and error.code == 'stale_lease':
            return {'state':'abandoned','job_id':job['id']}
        code = 'invalid_input' if isinstance(error, (ValueError, EmbeddingError)) else 'temporarily_unavailable'
        if isinstance(error, RepositoryError):
            code = error.code
        if isinstance(error, ProviderFailure):
            code = error.code
        if isinstance(error, InferenceError) and str(error) == 'deadline_exceeded':
            code = 'timeout'
        try:
            state = repository.call('fail_text_job', *args, code)
            return {'state':state,'job_id':job['id'],'error_code':code}
        except RepositoryError:
            # Unknown commit outcome or lost database connection: lease recovery
            # resolves it. Never overwrite another attempt or report false failure.
            return {'state':'abandoned','job_id':job['id']}
