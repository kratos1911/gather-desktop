"""Token-bounded source slices for trusted server-side ingestion; no truncation."""

import hashlib

from services.inference.runtime import MODEL, REVISION

VERSION = 'qwen-boundary-512-overlap64-v1'
MAX_TOKENS = 512
MAX_BYTES = 8192


def chunk_document(text, count_tokens):
    """The callback is the pinned document tokenizer, including special tokens.

    Exact Unicode-code-point offsets preserve provenance. Each result is intended
    for one embedding request. Existing parser/index formats are not rewritten.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError('empty_document')
    if len(text.encode('utf-8')) > 65536:
        raise ValueError('document_too_large')
    source_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()

    def fits(piece):
        if len(piece.encode('utf-8')) > MAX_BYTES:
            return False
        count = count_tokens(piece)
        if type(count) is not int or count <= 0:
            raise ValueError('invalid_token_count')
        return count <= MAX_TOKENS

    chunks, start = [], 0
    while start < len(text):
        # Search for a fitting prefix, not necessarily the longest possible one:
        # token counts need not be monotonic. Every returned slice is rechecked.
        low, high, end = start + 1, min(len(text), start + MAX_BYTES), start
        while low <= high:
            middle = (low + high) // 2
            if fits(text[start:middle]):
                end, low = middle, middle + 1
            else:
                high = middle - 1
        if end == start:
            raise ValueError('cannot_fit_character')
        if end < len(text):
            for separator in ('\n\n', '\n', ' '):
                boundary = text.rfind(separator, start + (end - start) // 2, end)
                candidate = boundary + len(separator)
                if boundary != -1 and fits(text[start:candidate]):
                    end = candidate
                    break
        piece = text[start:end]
        if not piece.strip():
            raise ValueError('unsearchable_whitespace_chunk')
        if not fits(piece):
            raise ValueError('chunk_budget_failed')
        identity = f'{MODEL}:{REVISION}:{VERSION}:{source_hash}:{start}:{end}'
        chunks.append({'id': hashlib.sha256(identity.encode()).hexdigest(),
                       'start': start, 'end': end, 'text': piece,
                       'tokens': count_tokens(piece), 'chunker_version': VERSION,
                       'offset_unit': 'unicode_code_point'})
        if len(chunks) > 256:
            raise ValueError('too_many_chunks')
        if end == len(text):
            break
        start = end - min(64, (end - start) // 4)
    return chunks
