"""Paired, offline chunk-policy experiment on frozen fictional sources only."""

import argparse
import base64
import json

from scripts.prepare_text_evaluation import corpus_hash, load_corpus
from scripts.score_text_evaluation import index_hash, lexical_run, score_run
from scripts.evaluate_vectors import vector_run, fuse_runs
from scripts.prepare_inference_image import ROOT, digest
from services.inference.chunking import chunk_document, VERSION
from services.inference.runtime import MODEL, REVISION, QUERY_TEMPLATE
from services.worker.text_processing import process_request, CHUNKER_VERSION

OUT = ROOT / 'output/inference-results/chunk-retrieval-v1'
FIXTURE = ROOT / 'tests/evaluation/chunk-boundaries-v1.json'
POLICIES = ('legacy', 'token512')
IMAGE = 'sha256:5d84bdf24729cacb20389734baee56fd49293eeb1bd2053d5eac1d0259c04f95'


def boundary_corpus():
    corpus = json.loads(FIXTURE.read_text(encoding='utf-8'))
    freeze = json.loads(FIXTURE.with_suffix('.freeze.json').read_text(encoding='utf-8'))
    if corpus_hash(corpus) != freeze['corpus_sha256']:
        raise ValueError('Boundary corpus changed; create a new version')
    return corpus


def prepare_layout(corpus, policy, count_tokens):
    """Preserve source labels; a quote split by a policy stays a strict miss."""
    if policy not in POLICIES:
        raise ValueError('Unknown chunk policy')
    meta = {'corpus_version': corpus['version'], 'corpus_sha256': corpus_hash(corpus)}
    documents, sources = [], {}
    for source in corpus['documents']:
        if source['id'] in sources:
            raise ValueError('Duplicate source')
        sources[source['id']] = source['text']
        request = {'version': 1, 'request_id': 'chunk-evaluation', 'format': source['format'],
                   'content_base64': base64.b64encode(source['text'].encode('utf-8')).decode()}
        result = process_request(json.dumps(request).encode())
        if result['status'] != 'processed':
            raise ValueError('Fixture rejected by text processor')
        document = {'id': source['id'], **result['document']}
        if policy == 'token512':
            document['chunks'] = chunk_document(source['text'], count_tokens)
            document['chunker_version'] = VERSION
        documents.append(document)
    by_id = {doc['id']: doc for doc in documents}
    labels, queries = [], []
    for query in corpus['queries']:
        if any(q['id'] == query['id'] for q in queries):
            raise ValueError('Duplicate query')
        if (query['category'] == 'absent') != (not query['expected']):
            raise ValueError('Only absent queries may lack evidence')
        if not query['text'].strip() or (not query['expected'] and not query.get('reason')):
            raise ValueError('Query text or absent rationale missing')
        evidence = []
        for item in query['expected']:
            text, quote = sources[item['document_id']], item['quote']
            if not quote or text.count(quote) != 1:
                raise ValueError('Evidence must occur exactly once')
            start = text.index(quote)
            end = start + len(quote)
            acceptable = [chunk['id'] for chunk in by_id[item['document_id']]['chunks']
                          if chunk['start'] <= start and chunk['end'] >= end]
            evidence.append({'document_id': item['document_id'], 'quote': quote,
                             'start': start, 'end': end, 'acceptable_chunk_ids': acceptable})
        labels.append({'id': query['id'], 'category': query['category'], 'evidence': evidence,
                       'absent_reason': query.get('reason')})
        queries.append({'id': query['id'], 'text': query['text']})
    return {'index': {**meta, 'documents': documents}, 'queries': {**meta, 'queries': queries},
            'labels': {**meta, 'queries': labels}}


def span_covered(evidence, hits, chunks):
    """Union of retrieved same-source intervals must cover every evidence character."""
    intervals = sorted((chunks[(hit['document_id'], hit['chunk_id'])]['start'],
                        chunks[(hit['document_id'], hit['chunk_id'])]['end'])
                       for hit in hits if hit['document_id'] == evidence['document_id'])
    cursor = evidence['start']
    for start, end in intervals:
        if end <= cursor:
            continue
        if start > cursor:
            return False
        cursor = max(cursor, end)
        if cursor >= evidence['end']:
            return True
    return False


def coverage_report(prepared, run):
    # Reuse strict validation before reading ranked identities.
    report = score_run(prepared['index'], prepared['labels'], run)
    chunks = {(doc['id'], chunk['id']): chunk for doc in prepared['index']['documents']
              for chunk in doc['chunks']}
    hits = {row['id']: row['hits'][:5] for row in run['results']}
    coverage = []
    for row, label in zip(report['queries'], prepared['labels']['queries']):
        evidence = label['evidence']
        union = (sum(span_covered(item, hits[label['id']], chunks) for item in evidence)
                 / len(evidence)) if evidence else None
        row['union_evidence_recall_at_5'] = union
        if union is not None:
            coverage.append(union)
    report['summary']['union_evidence_recall_at_5'] = sum(coverage) / len(coverage) if coverage else None
    report['structurally_uncontained'] = [
        {'query_id': query['id'], 'document_id': item['document_id'],
         'start': item['start'], 'end': item['end']}
        for query in prepared['labels']['queries'] for item in query['evidence']
        if not item['acceptable_chunk_ids']]
    return report


def build_experiment(count_tokens):
    datasets = {'text-v2': load_corpus('text-v2'), 'boundaries-v1': boundary_corpus()}
    layouts, requests, positions = {}, [], {}
    for name, corpus in datasets.items():
        layouts[name] = {}
        for policy in POLICIES:
            prepared = prepare_layout(corpus, policy, count_tokens)
            layouts[name][policy] = prepared
            items = [('document', chunk['text']) for doc in prepared['index']['documents']
                     for chunk in doc['chunks']]
            items += [('query', query['text']) for query in prepared['queries']['queries']]
            for role, text in items:
                if (role, text) not in positions:
                    prompted = QUERY_TEMPLATE.format(text=text) if role == 'query' else text
                    tokens = count_tokens(prompted)
                    if not 0 < tokens <= 512:
                        raise ValueError('Experiment item exceeds 512 tokens')
                    positions[(role, text)] = len(requests)
                    requests.append({'role': role, 'texts': [text]})
    return layouts, requests


def tokenizer_counter():
    from tokenizers import Tokenizer
    tokenizer = Tokenizer.from_file(str(ROOT / 'output/inference-model/tokenizer.json'))
    return lambda text: len(tokenizer.encode(text).ids)


def prepare_experiment():
    count = tokenizer_counter()
    layouts, requests = build_experiment(count)
    plan = {'schema_version': 1, 'model': MODEL, 'revision': REVISION, 'image_id': IMAGE,
            'policies': {'legacy': CHUNKER_VERSION, 'token512': VERSION},
            'datasets': {name: {policy: {'corpus_sha256': p['index']['corpus_sha256'],
                'index_sha256': index_hash(p['index']),
                'chunks': sum(len(d['chunks']) for d in p['index']['documents'])}
                for policy, p in pair.items()} for name, pair in layouts.items()},
            'requests_sha256': index_hash(requests), 'unique_requests': len(requests),
            'token_counts': [count(QUERY_TEMPLATE.format(text=r['texts'][0])
                                  if r['role'] == 'query' else r['texts'][0]) for r in requests],
            'protocol_sha256': digest(ROOT / 'tests/evaluation/CHUNK_RETRIEVAL_PROTOCOL.md')}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / 'plan.json'
    if path.exists() and json.loads(path.read_text()) != plan:
        raise ValueError('Frozen experiment changed; use a new version/output location')
    path.write_text(json.dumps(plan, indent=2) + '\n')
    return layouts, requests, plan


def score_experiment():
    layouts, requests, plan = prepare_experiment()
    raw_path = ROOT / 'output/inference-results/patched/retrieval-rows.json'
    raw = json.loads(raw_path.read_text())
    runtime = json.loads(raw_path.with_name('qwen-retrieval.json').read_text())
    if (not runtime['passed'] or runtime.get('experiment_sha256') != index_hash(plan)
            or runtime['image_id'] != IMAGE or runtime.get('raw_rows_sha256') != digest(raw_path)):
        raise ValueError('Matching completed runtime evidence required')
    replies = [row['result'] for row in raw if 'result' in row]
    if len(replies) != len(requests):
        raise ValueError('Incomplete experiment')
    vectors = {}
    for request, reply, count in zip(requests, replies, plan['token_counts']):
        if (reply['model'], reply['revision'], reply['dimensions'], reply['prompt_tokens']) != (MODEL, REVISION, 512, count):
            raise ValueError('Model identity/token count mismatch')
        vectors[(request['role'], request['texts'][0])] = reply['data'][0]['embedding']
    space = {'provider': 'self-hosted-cpu', 'model': MODEL, 'revision': REVISION,
             'dimensions': 512, 'query_template': QUERY_TEMPLATE, 'document_template': '{text}',
             'tokenizer_revision': REVISION}
    reports, runs = {}, {}
    for name, pair in layouts.items():
        reports[name], runs[name] = {}, {}
        for policy, p in pair.items():
            index, queries = p['index'], p['queries']
            def vector(role, text):
                return {'vector': vectors[(role, text)], 'embedding_space': space, 'truncated': False}
            artifact = {'schema_version': 1, 'provenance': 'model_export', 'embedding_space': space,
                'corpus_version': index['corpus_version'], 'corpus_sha256': index['corpus_sha256'],
                'index_sha256': index_hash(index),
                'documents': [{'document_id': d['id'], 'chunk_id': c['id'], **vector('document', c['text'])}
                              for d in index['documents'] for c in d['chunks']],
                'queries': [{'id': q['id'], **vector('query', q['text'])} for q in queries['queries']]}
            dense, lexical = vector_run(index, queries, artifact), lexical_run(index, queries)
            hybrid = fuse_runs(index, p['labels'], lexical, dense)
            runs[name][policy] = {'dense': dense, 'lexical': lexical, 'hybrid': hybrid}
            reports[name][policy] = {method: coverage_report(p, run)
                                    for method, run in runs[name][policy].items()}
    old = reports['text-v2']['legacy']['dense']['summary']
    new = reports['text-v2']['token512']['dense']['summary']
    metrics = ('document_recall_at_5', 'document_mrr_at_5', 'evidence_recall_at_5')
    gates = {metric: new[metric] >= .90 and new[metric] - old[metric] >= -.02 for metric in metrics}
    report = {'scope': 'paired synthetic chunk-policy evaluation; not public quality or deployment approval',
              'plan': plan, 'runtime': runtime, 'raw_rows_sha256': digest(raw_path),
              'reports': reports, 'text_v2_gates': gates, 'passed': all(gates.values()),
              'boundary_stress_is_diagnostic': True}
    (OUT / 'rankings.json').write_text(json.dumps(runs, indent=2) + '\n')
    (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'gates': gates,
        'summaries': {name: {policy: {method: value['summary'] for method, value in methods.items()}
                            for policy, methods in pair.items()} for name, pair in reports.items()}}, indent=2))
    if not report['passed']:
        raise SystemExit('Chunk policy did not pass predeclared gate; evidence retained')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--score', action='store_true')
    args = parser.parse_args()
    if args.score:
        score_experiment()
    else:
        _, _, plan = prepare_experiment()
        print(json.dumps(plan, indent=2))


if __name__ == '__main__':
    main()
