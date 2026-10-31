"""Internal query orchestration. No default provider, credentials or public route.

api(method, path, payload) must be a trusted, bounded transport permanently bound
to ONE user's bearer session (never a service key). It decodes JSON, rejects HTTP
errors, forbids redirects and does not log bodies. SessionClient implements this
contract; hosted transport and deployment verification remain pending.
Provider uses the same explicit infer/count_tokens contract as ingestion.
"""
import math
import threading
from uuid import UUID

from services.inference.runtime import MODEL, REVISION, DIMENSIONS, validate_request
from services.worker.embedding_client import embed_texts, Limits
from services.worker.search_context import (
    MAX_CANDIDATES, MAX_SOURCES, Hit, Passage, Snapshot, assemble_context,
)
from services.worker.source_listing import page, parameters
from services.worker.model_availability import ModelServiceError
from services.worker.pdf_processing import enrich_published


class SearchError(Exception):
    """Content-free failure; never expose transport errors or source text."""


def _uuid(value):
    if not isinstance(value, str) or str(UUID(value)) != value:
        raise ValueError('invalid_identity')
    return value


def search(query, *, api, provider, limit=20, cancel=None):
    """Owned metadata preflight, at most one embedding/ranking and five reads.

    No automatic retries, model startup, synthetic fallback or owner payload.
    Cancellation is checked between calls and forwarded to inference. Transport
    must impose its own I/O deadlines; this function cannot stop arbitrary I/O.
    """
    cancel = cancel if cancel is not None else threading.Event()

    def active():
        if cancel.is_set():
            raise SearchError('cancelled')

    def call(method, path, payload=None):
        active()
        result = api(method, path, payload)
        active()
        return result

    stage = 'session'
    try:
        active()
        if type(limit) is not int or not 1 <= limit <= MAX_CANDIDATES:
            raise SearchError('invalid_query')
        request = {'role': 'query', 'texts': [query]}
        try:
            templated = validate_request(request)[0]
        except Exception:
            raise SearchError('invalid_query') from None
        # Auth verifies the bearer session before any inference is requested.
        owner = _uuid(call('GET', '/auth/v1/user')['id'])

        # Reuse the owner-scoped metadata contract before spending inference.
        # Only a complete page proves emptiness. If there may be more sources,
        # preserve normal search rather than miss a publication on a later page.
        stage = 'retrieval'
        listing = page(call('POST','/rest/v1/rpc/list_library_sources',parameters()))
        if listing['next_cursor'] is None and not any(
                row['published_version_id'] is not None for row in listing['items']):
            active()
            context = assemble_context(owner,[],[])
            active()
            return context

        def send(_body):
            active()
            result = provider.infer(request, cancel=cancel)
            active()
            if not isinstance(result, dict) or (
                result.get('model'), result.get('revision'), result.get('dimensions')
            ) != (MODEL, REVISION, DIMENSIONS):
                raise ValueError('model_identity')
            return result

        # Count the exact query template, but send RAW text with role=query so
        # Runtime applies that template once. Preserve its 2048-token ceiling.
        stage = 'model'
        vector = embed_texts([templated], model=MODEL,
            limits=Limits(DIMENSIONS, 2048, 2048, 1, 1),
            count_tokens=provider.count_tokens, send=send)['vectors'][0]
        if abs(math.hypot(*vector) - 1) > .001:
            raise ValueError('invalid_vector_norm')
        stage = 'retrieval'
        rows = call('POST', '/rest/v1/rpc/search_published_text', {
            'p_query': vector, 'p_model': MODEL, 'p_revision': REVISION,
            'p_dimensions': DIMENSIONS, 'p_limit': limit,
        })
        if not isinstance(rows, list) or len(rows) > limit:
            raise ValueError('candidate_limit')
        selected, omitted, seen, previous_score = {}, [], set(), math.inf
        for row in rows:
            sid, vid = _uuid(row['source_id']), _uuid(row['version_id'])
            pid = row['passage_id']
            score = row['similarity']
            if (not isinstance(pid, str) or not 0 < len(pid) <= 128
                    or (sid, vid, pid) in seen
                    or (row['model_id'], row['model_revision'], row['dimensions']) != (MODEL, REVISION, DIMENSIONS)
                    or type(score) not in (float, int) or not math.isfinite(score)
                    or not -1.000001 <= score <= 1.000001 or score > previous_score
                    or not isinstance(row['title'], str) or len(row['title']) > 500
                    or not isinstance(row['body'], str) or len(row['body'].encode('utf-8')) > 8192
                    or type(row['start_offset']) is not int or type(row['end_offset']) is not int
                    or not 0 <= row['start_offset'] < row['end_offset'] <= 65536
                    or not isinstance(row['source_sha256'], str) or len(row['source_sha256']) != 64):
                raise ValueError('invalid_candidate')
            previous_score = score
            seen.add((sid, vid, pid))
            if sid in selected:
                if selected[sid][0]['version_id'] != vid:
                    raise ValueError('mixed_versions')
                selected[sid].append(row)
            elif len(selected) < MAX_SOURCES:
                selected[sid] = [row]
            elif sid not in {item['source_id'] for item in omitted}:
                omitted.append({'source_id': sid, 'reason': 'source_limit'})

        snapshots, metadata = [], {}
        for sid, candidates in selected.items():
            stage = 'source_open'
            seed = candidates[0]
            docs = call('POST', '/rest/v1/rpc/open_published_text', {
                'p_source': sid, 'p_version': seed['version_id'],
            })
            docs=enrich_published(call,sid,seed['version_id'],docs)
            if docs == []:
                omitted.append({'source_id': sid, 'reason': 'no_longer_available'})
                continue
            if not isinstance(docs, list) or len(docs) != 1:
                raise ValueError('invalid_snapshot')
            doc = docs[0]
            if (doc['source_id'], doc['version_id'], doc['source_sha256'],
                doc['model_id'], doc['model_revision'], doc['dimensions']) != (
                sid, seed['version_id'], seed['source_sha256'], MODEL, REVISION, DIMENSIONS):
                raise ValueError('snapshot_identity')
            if not isinstance(doc['passages'], list) or not 1 <= len(doc['passages']) <= 256:
                raise ValueError('passage_limit')
            passages = tuple(Passage(p['id'], p['start'], p['end']) for p in doc['passages'])
            by_id = {p.id: p for p in passages}
            for row in candidates:
                p = by_id.get(row['passage_id'])
                if (p is None or (p.start, p.end) != (row['start_offset'], row['end_offset'])
                        or row['source_sha256'] != doc['source_sha256']
                        or doc['body'][p.start:p.end] != row['body']):
                    raise ValueError('citation_mismatch')
            snapshots.append(Snapshot(owner, sid, doc['version_id'], doc['source_sha256'], doc['body'], passages,
                text_sha256=doc.get('text_sha256'),media_type=doc.get('media_type','text/plain'),
                pages=tuple((p['number'],p['start'],p['end']) for p in doc.get('pages',[]))))
            metadata[sid] = {'title': seed['title'], 'similarity': seed['similarity']}
        active()
        # Preserve original ranking even when several hits share one source.
        stage = 'context'
        visible = {source.source_id for source in snapshots}
        hits = [Hit(owner, row['source_id'], row['version_id'], row['passage_id'])
                for row in rows if row['source_id'] in visible]
        context = assemble_context(owner, hits, snapshots)
        context['omitted_sources'].extend(omitted)
        for window in context['windows']:
            window.update(metadata[window['source_id']])
            window['seed_rank'] = next(i for i, row in enumerate(rows, 1)
                if row['source_id'] == window['source_id'])
        active()
        return context
    except SearchError:
        raise
    except Exception as error:
        if cancel.is_set():
            raise SearchError('cancelled') from None
        if stage=='model' and isinstance(error,ModelServiceError):
            raise SearchError(error.reason) from None
        code = {'session':'session_unavailable','model':'model_unavailable',
                'retrieval':'library_unavailable','source_open':'library_unavailable',
                'context':'search_failed'}.get(stage,'search_failed')
        raise SearchError(code) from None
