"""Offline saved-Qwen score calibration/regression replay; zero inference calls."""
import hashlib
import json
import math
from pathlib import Path

from scripts.prepare_text_evaluation import load_corpus, corpus_hash
from scripts.evaluate_chunk_retrieval import boundary_corpus
from scripts.evaluate_search_context import evaluate
from services.worker.search_relevance import (
    VERSION, MIN_SIMILARITY, MAX_SCORE_GAP, selected_indices, validate_space,
)

ROOT = Path(__file__).resolve().parents[1]
RANKINGS_SHA256 = 'b47eea523fc6971063ae357ebaa0660d52443e729bb21c37c18006e9486298cf'


def filter_hits(hits):
    return [hits[i] for i in selected_indices([h['score'] for h in hits])]


def metrics(run, labels, filtered):
    totals = dict(answerable=0, source_recalled=0, returned=0,
                  expected_source_candidates=0, absent=0, absent_empty=0)
    misses = []
    for row in run['results']:
        # Compare the same candidate depth before/after filtering.
        hits = row['hits'][:5]
        if filtered:
            hits = filter_hits(hits)
        expected = {x['document_id'] for x in labels[row['id']]['expected']}
        found = {h['document_id'] for h in hits}
        if expected:
            totals['answerable'] += 1
            totals['source_recalled'] += expected <= found
            if not expected <= found:
                misses.append(row['id'])
        else:
            totals['absent'] += 1
            totals['absent_empty'] += not hits
        totals['returned'] += len(hits)
        totals['expected_source_candidates'] += sum(h['document_id'] in expected for h in hits)
    return dict(totals, missing_expected_sources=misses)


def main():
    path = ROOT / 'output/inference-results/chunk-retrieval-v1/rankings.json'
    if path.stat().st_size > 8*1024*1024 or hashlib.sha256(path.read_bytes()).hexdigest() != RANKINGS_SHA256:
        raise ValueError('reviewed_saved_rankings_required')
    ranks = json.loads(path.read_text())
    corpora = {'text-v2': load_corpus('text-v2'), 'boundaries-v1': boundary_corpus()}
    datasets = {}
    points = []
    for name, corpus in corpora.items():
        run = ranks[name]['token512']['dense']
        space = run['embedding_space']
        validate_space(space['model'], space['revision'], space['dimensions'])
        if run['provenance'] != 'model_export' or run['corpus_sha256'] != corpus_hash(corpus):
            raise ValueError('saved_corpus_or_vector_provenance_changed')
        labels = {q['id']: q for q in corpus['queries']}
        if {q['id'] for q in run['results']} != set(labels):
            raise ValueError('incomplete_queries')
        if name == 'text-v2':
            for row in run['results']:
                for source in {x['document_id'] for x in labels[row['id']]['expected']}:
                    best = max(h['score'] for h in row['hits'][:5] if h['document_id'] == source)
                    points.append((best, row['hits'][0]['score'] - best))
        datasets[name] = {'baseline': metrics(run, labels, False),
                          'filtered': metrics(run, labels, True)}
    # Post-hoc calibration on known text-v2: preserve each labelled source found
    # in top5, with a .02 safety allowance, rounding outward to .01 increments.
    derived = (math.floor((min(p[0] for p in points)-.02)*100)/100,
               math.ceil((max(p[1] for p in points)+.02)*100)/100)
    if derived != (MIN_SIMILARITY, MAX_SCORE_GAP):
        raise ValueError('profile_does_not_match_calibration')
    out = ROOT / 'output/evaluation/relevance-v1'
    baseline = evaluate(destination=out/'context-baseline', emit=False)
    filtered = evaluate(filter_hits=filter_hits, destination=out/'context-filtered', emit=False)
    regressions = []
    for name in datasets:
        old = {q['id']: q for q in baseline['datasets'][name]['queries']}
        lost = [q['id'] for q in filtered['datasets'][name]['queries']
                if q['context_evidence_recall'] is not None
                and q['context_evidence_recall'] < old[q['id']]['context_evidence_recall']]
        datasets[name]['context_regressions'] = lost
        datasets[name]['context_recall'] = filtered['datasets'][name]['context_evidence_recall']
        regressions += lost
    report = dict(policy=VERSION, minimum_similarity=MIN_SIMILARITY,
        maximum_score_gap=MAX_SCORE_GAP, datasets=datasets,
        scope='Known fictional regression sets; post-hoc calibration, not independent quality validation',
        rankings_sha256=RANKINGS_SHA256, raw_vectors_sha256=baseline['raw_vectors_sha256'],
        new_model_calls=0, passed=not regressions)
    out.mkdir(parents=True, exist_ok=True)
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    if regressions:
        raise SystemExit('Context coverage regressed; do not enable this profile')


if __name__ == '__main__':
    main()
