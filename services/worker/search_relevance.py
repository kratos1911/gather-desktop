"""Bound semantic candidates for the pinned Qwen text space."""
import math
import re
from unicodedata import normalize

VERSION = 'qwen-cosine-window-v1'
MIN_SIMILARITY = 0.24
MAX_SCORE_GAP = 0.12
UNANCHORED_MIN_SIMILARITY = 0.65
EMBEDDING_SPACE = ('Qwen/Qwen3-Embedding-0.6B',
    '97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3', 512)
_WORDS = re.compile(r'[^\W_]+')
_STOP_WORDS = frozenset('''
    a an and are as at be been before besides both by can come comes could did
    do does doing each for former from go goes going had has have he hence her
    here how i if in includes into is it its leave look may me must my no not
    of on once or our out over per put receive said say see shall should since
    so some someone something stay than that the their them there these they
    this those through time to too under up upon use was we were what when where
    which while who whom why will with without would you your after current
    exact old prior previously find show tell keep
'''.split())


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


def _content_terms(text):
    terms = set()
    for word in _WORDS.findall(normalize('NFKC', text).casefold()):
        if word in _STOP_WORDS or (len(word) < 3 and not word.isdecimal()):
            continue
        # Normalize common English plural endings for lexical corroboration.
        if len(word) > 4 and word.isascii() and word.endswith('ies'):
            word = word[:-3] + 'y'
        elif len(word) > 3 and word.isascii() and word.endswith('s') and not word.endswith(('ss', 'us', 'is')):
            word = word[:-1]
        if word not in _STOP_WORDS:
            terms.add(word)
    return terms


def supported_semantic(query, candidates):
    """Filter ordered hybrid candidates before applying the near-best band."""
    terms = _content_terms(query)
    supported = [row for row in candidates
                 if not terms or row['similarity'] >= UNANCHORED_MIN_SIMILARITY
                 or terms.intersection(_content_terms(row['title'] + '\n' + row['body']))]
    accepted = selected_indices([row['similarity'] for row in supported])
    return [supported[i] for i in accepted]
