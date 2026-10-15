"""Replay verified fictional embeddings; no model load, Docker or network."""
import json

from scripts.evaluate_chunk_retrieval import build_experiment, tokenizer_counter, IMAGE
from scripts.evaluate_vectors import vector_run
from scripts.score_text_evaluation import index_hash
from scripts.prepare_inference_image import ROOT, digest
from services.inference.runtime import MODEL, REVISION, QUERY_TEMPLATE
from services.worker.search_context import (assemble_context, Snapshot, Passage, Hit, VERSION,
    MAX_CANDIDATES, MAX_SOURCES, MAX_WINDOW_BYTES, MAX_TOTAL_BYTES)


def evaluate():
    evidence_path = ROOT / 'tests/evaluation/results/chunk-retrieval-20261015.json'
    evidence = json.loads(evidence_path.read_text())
    raw_path = ROOT / 'output/inference-results/patched/retrieval-rows.json'
    if (digest(raw_path) != evidence['raw_rows_sha256'] or not evidence['runtime']['passed']
            or evidence['runtime']['image_id'] != IMAGE):
        raise ValueError('Verified complete embedding evidence required')
    layouts, requests = build_experiment(tokenizer_counter())
    plan = evidence['plan']
    if index_hash(requests) != plan['requests_sha256']:
        raise ValueError('Embedding inputs changed; cannot reuse vectors')
    replies = [row['result'] for row in json.loads(raw_path.read_text()) if 'result' in row]
    if len(replies) != len(requests):
        raise ValueError('Incomplete vectors')
    vectors = {}
    for request, reply, tokens in zip(requests, replies, plan['token_counts']):
        if (reply['model'], reply['revision'], reply['dimensions'], reply['prompt_tokens']) != (MODEL, REVISION, 512, tokens):
            raise ValueError('Incompatible saved vector')
        vectors[(request['role'], request['texts'][0])] = reply['data'][0]['embedding']
    space = {'provider': 'self-hosted-cpu', 'model': MODEL, 'revision': REVISION,
             'dimensions': 512, 'query_template': QUERY_TEMPLATE, 'document_template': '{text}',
             'tokenizer_revision': REVISION}
    datasets = {}
    for name, pair in layouts.items():
        p = pair['token512']
        index, queries = p['index'], p['queries']
        if index_hash(index) != plan['datasets'][name]['token512']['index_sha256']:
            raise ValueError('Saved vector index mismatch')
        def vector(role, text):
            return {'vector': vectors[(role, text)], 'embedding_space': space, 'truncated': False}
        artifact = {'schema_version': 1, 'provenance': 'model_export', 'embedding_space': space,
            'corpus_version': index['corpus_version'], 'corpus_sha256': index['corpus_sha256'],
            'index_sha256': index_hash(index),
            'documents': [{'document_id': d['id'], 'chunk_id': c['id'], **vector('document', c['text'])}
                          for d in index['documents'] for c in d['chunks']],
            'queries': [{'id': q['id'], **vector('query', q['text'])} for q in queries['queries']]}
        dense = vector_run(index, queries, artifact)
        snapshots = []
        for doc in index['documents']:
            # Reconstruct exact source from ordered overlapping fixture slices.
            text, end = '', 0
            for chunk in doc['chunks']:
                if chunk['start'] > end:
                    raise ValueError('Fixture source gap')
                if text[chunk['start']:end] != chunk['text'][:end - chunk['start']]:
                    raise ValueError('Fixture overlap mismatch')
                text += chunk['text'][end - chunk['start']:]
                end = chunk['end']
            snapshots.append(Snapshot('fixture-owner', doc['id'], doc['source_sha256'],
                doc['source_sha256'], text, tuple(Passage(c['id'], c['start'], c['end']) for c in doc['chunks'])))
        sources = {s.source_id: s for s in snapshots}
        labels = {q['id']: q for q in p['labels']['queries']}
        old_rows = {q['id']: q for q in evidence['reports'][name]['token512']['dense']['queries']}
        rows = []
        for row in dense['results']:
            hits = [Hit('fixture-owner', h['document_id'], sources[h['document_id']].version_id,
                        h['chunk_id']) for h in row['hits'][:MAX_CANDIDATES]]
            result = assemble_context('fixture-owner', hits, snapshots)
            expected = labels[row['id']]['evidence']
            covered = [any(w['source_id'] == item['document_id'] and w['start'] <= item['start']
                           and w['end'] >= item['end'] for w in result['windows']) for item in expected]
            old = old_rows[row['id']]
            rows.append({'id': row['id'], 'baseline_strict_evidence': old['evidence_recall_at_5'],
                'baseline_union_evidence': old['union_evidence_recall_at_5'],
                'context_evidence_recall': sum(covered) / len(covered) if covered else None,
                'utf8_bytes': result['utf8_bytes'], 'omitted_sources': result['omitted_sources'],
                'windows': [{k: v for k, v in w.items() if k != 'text'} for w in result['windows']]})
        answerable = [q for q in rows if q['context_evidence_recall'] is not None]
        datasets[name] = {'queries': rows, 'answerable': len(answerable),
            'context_evidence_recall': sum(q['context_evidence_recall'] for q in answerable) / len(answerable),
            'baseline_strict_evidence': evidence['reports'][name]['token512']['dense']['summary']['evidence_recall_at_5'],
            'baseline_union_evidence': evidence['reports'][name]['token512']['dense']['summary']['union_evidence_recall_at_5'],
            'regressions_vs_union': [q['id'] for q in answerable if q['context_evidence_recall'] < q['baseline_union_evidence']],
            'remaining_misses': [q['id'] for q in answerable if q['context_evidence_recall'] < 1],
            'absent_returning_context': sum(bool(q['windows']) for q in rows if q['context_evidence_recall'] is None),
            'maximum_output_bytes': max(q['utf8_bytes'] for q in rows)}
    report = {'scope': 'Known synthetic regression replay; expanded context is not original passage recall',
        'policy': VERSION, 'limits': {'candidates': MAX_CANDIDATES, 'sources': MAX_SOURCES,
                                     'window_bytes': MAX_WINDOW_BYTES, 'total_bytes': MAX_TOTAL_BYTES},
        'source_evidence_sha256': digest(evidence_path), 'raw_vectors_sha256': digest(raw_path),
        'new_model_calls': 0, 'datasets': datasets}
    destination = ROOT / 'output/evaluation/search-context-v1'
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({name: {k: v for k, v in d.items() if k != 'queries'} for name, d in datasets.items()}, indent=2))


if __name__ == '__main__':
    evaluate()
