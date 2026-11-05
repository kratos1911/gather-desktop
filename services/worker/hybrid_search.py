"""Bounded reciprocal rank fusion; cosine scores keep their original meaning."""
from services.worker.search_context import MAX_CANDIDATES


def fuse(semantic, keywords, limit):
    if len(semantic)+len(keywords) > MAX_CANDIDATES:
        raise ValueError('candidate_limit')
    rows, scores, first = {}, {}, {}
    for branch in (semantic, keywords):
        for rank, row in enumerate(branch, 1):
            key = (row['source_id'], row['version_id'], row['passage_id'])
            if key in rows and rows[key] != row:
                raise ValueError('conflicting_candidate')
            rows[key] = row
            scores[key] = scores.get(key, 0.) + 1/(60+rank)
            first[key] = min(first.get(key, rank), rank)
    keys = sorted(rows, key=lambda key:(-scores[key], first[key], key))
    return [rows[key] for key in keys[:limit]]
