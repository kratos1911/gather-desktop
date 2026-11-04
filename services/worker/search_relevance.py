"""Trusted score gate for the pinned Qwen text space; not answerability proof.

Calibrated on saved text-v2 vectors, with a separate boundary regression replay.
No model call, keyword requirement, user setting, normalization or score rewrite.
See docs/SEARCH_RELEVANCE.md for measured tradeoffs and remaining false matches.
"""
import math

VERSION = 'qwen-cosine-window-v1'
MIN_SIMILARITY = 0.24
MAX_SCORE_GAP = 0.12
EMBEDDING_SPACE = ('Qwen/Qwen3-Embedding-0.6B',
    '97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3', 512)


def validate_space(model, revision, dimensions):
    if (model, revision, dimensions) != EMBEDDING_SPACE:
        raise ValueError('uncalibrated_embedding_space')


def selected_indices(scores):
    """Keep bounded ranked candidates near the best score and above the floor."""
    if not isinstance(scores, (list, tuple)) or len(scores) > 100:
        raise ValueError('invalid_relevance_scores')
    previous = math.inf
    for score in scores:
        if (type(score) not in (int, float) or not math.isfinite(score)
                or not -1.000001 <= score <= 1.000001 or score > previous):
            raise ValueError('invalid_relevance_scores')
        previous = score
    if not scores:
        return ()
    cutoff = max(MIN_SIMILARITY, scores[0] - MAX_SCORE_GAP)
    return tuple(i for i, score in enumerate(scores) if score >= cutoff)
