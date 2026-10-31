"""Bounded reader context from authorized, immutable source snapshots.

The caller must obtain owner identity from authentication and snapshots from an
ownership-enforcing repository. This pure function is not authentication or RLS.
It never calls a model, changes rankings, or executes source text.
"""
from dataclasses import dataclass
import hashlib
import re
from services.worker.pdf_processing import validate_text

VERSION = 'source-neighbors-v1'
MAX_CANDIDATES = 100
MAX_SOURCES = 5
MAX_WINDOW_BYTES = 8192
MAX_TOTAL_BYTES = 32768


@dataclass(frozen=True)
class Passage:
    id: str
    start: int
    end: int


@dataclass(frozen=True)
class Snapshot:
    owner_id: str
    source_id: str
    version_id: str
    source_sha256: str
    text: str
    passages: tuple[Passage, ...]
    published: bool = True
    deleted: bool = False
    text_sha256: str | None = None
    media_type: str = 'text/plain'
    pages: tuple[tuple[int,int,int],...] = ()


@dataclass(frozen=True)
class Hit:
    owner_id: str
    source_id: str
    version_id: str
    passage_id: str


def _identity(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise ValueError('invalid_identity')


def assemble_context(owner_id, hits, snapshots):
    """One window per source, keeping first-hit source order.

At most one preceding and one following passage may expand the seed. Only
touching/overlapping intervals merge. Whole passages are accepted or omitted;
no hidden clipping, gaps, or second-hop expansion. All candidates are validated
before producing any output, including those beyond the first five sources.
"""
    _identity(owner_id)
    if not isinstance(hits, (list, tuple)) or len(hits) > MAX_CANDIDATES:
        raise ValueError('candidate_limit')
    if not isinstance(snapshots, (list, tuple)) or len(snapshots) > MAX_CANDIDATES:
        raise ValueError('snapshot_limit')
    sources = {}
    for source in snapshots:
        if not isinstance(source, Snapshot):
            raise ValueError('invalid_snapshot')
        for value in (source.owner_id, source.source_id, source.version_id):
            _identity(value)
        if source.owner_id != owner_id or source.published is not True or source.deleted is not False:
            raise ValueError('source_not_visible')
        if source.source_id in sources:
            raise ValueError('duplicate_source_version')
        if not isinstance(source.text, str) or len(source.text) > 65536 or not source.text.strip():
            raise ValueError('invalid_source_text')
        try:
            encoded = source.text.encode('utf-8')
        except UnicodeError:
            raise ValueError('invalid_source_text') from None
        if not isinstance(source.source_sha256,str) or not re.fullmatch('[0-9a-f]{64}',source.source_sha256):
            raise ValueError('source_integrity')
        if source.media_type=='application/pdf':
            if not isinstance(source.pages,tuple): raise ValueError('source_integrity')
            validate_text(source.text,[dict(number=n,start=a,end=b) for n,a,b in source.pages],source.text_sha256)
        elif source.media_type!='text/plain' or source.text_sha256 is not None or source.pages or len(encoded)>65536 or hashlib.sha256(encoded).hexdigest()!=source.source_sha256:
            raise ValueError('source_integrity')
        if not isinstance(source.passages, tuple) or not 1 <= len(source.passages) <= 256:
            raise ValueError('passage_limit')
        positions, previous = {}, None
        for index, passage in enumerate(source.passages):
            if not isinstance(passage, Passage):
                raise ValueError('invalid_passage')
            _identity(passage.id)
            if (passage.id in positions or type(passage.start) is not int or type(passage.end) is not int
                    or not 0 <= passage.start < passage.end <= len(source.text)):
                raise ValueError('invalid_passage_range')
            if previous and (passage.start <= previous.start or passage.end <= previous.end):
                raise ValueError('unordered_passages')
            if len(source.text[passage.start:passage.end].encode('utf-8')) > MAX_WINDOW_BYTES:
                raise ValueError('oversized_passage')
            positions[passage.id] = index
            previous = passage
        sources[source.source_id] = source, positions
    for hit in hits:
        if not isinstance(hit, Hit) or hit.owner_id != owner_id:
            raise ValueError('hit_not_visible')
        for value in (hit.source_id, hit.version_id, hit.passage_id):
            _identity(value)
        if hit.source_id not in sources:
            raise ValueError('missing_source')
        source, positions = sources[hit.source_id]
        if hit.version_id != source.version_id or hit.passage_id not in positions:
            raise ValueError('stale_or_unknown_passage')

    # Reserve whole seed windows first so expansion cannot starve later sources.
    selected, seen, used, omitted = [], set(), 0, []
    for rank, hit in enumerate(hits, 1):
        if hit.source_id in seen:
            continue
        seen.add(hit.source_id)
        if len(selected) == MAX_SOURCES:
            omitted.append({'source_id': hit.source_id, 'reason': 'source_limit'})
            continue
        source, positions = sources[hit.source_id]
        position = positions[hit.passage_id]
        seed = source.passages[position]
        size = len(source.text[seed.start:seed.end].encode('utf-8'))
        if used + size > MAX_TOTAL_BYTES:
            omitted.append({'source_id': hit.source_id, 'reason': 'total_byte_limit'})
            continue
        used += size
        selected.append({'source': source, 'position': position, 'rank': rank,
                         'start': seed.start, 'end': seed.end, 'bytes': size,
                         'included': [seed.id], 'skipped': []})
    for window in selected:
        source, position = window['source'], window['position']
        for neighbor in (position - 1, position + 1):
            if not 0 <= neighbor < len(source.passages):
                continue
            passage = source.passages[neighbor]
            reason = None
            start, end = min(window['start'], passage.start), max(window['end'], passage.end)
            size = len(source.text[start:end].encode('utf-8'))
            if passage.start > window['end'] or passage.end < window['start']:
                reason = 'gap'
            elif size > MAX_WINDOW_BYTES:
                reason = 'window_byte_limit'
            elif used + size - window['bytes'] > MAX_TOTAL_BYTES:
                reason = 'total_byte_limit'
            if reason:
                window['skipped'].append({'passage_id': passage.id, 'reason': reason})
                continue
            used += size - window['bytes']
            window.update(start=start, end=end, bytes=size)
            window['included'].append(passage.id)
    windows = []
    for window in selected:
        source = window['source']
        windows.append({'owner_id': owner_id, 'source_id': source.source_id,
            'version_id': source.version_id, 'source_sha256': source.source_sha256,
            'seed_passage_id': source.passages[window['position']].id,
            'seed_rank': window['rank'], 'passage_ids': window['included'],
            'start': window['start'], 'end': window['end'], 'offset_unit': 'unicode_code_point',
            'text': source.text[window['start']:window['end']], 'utf8_bytes': window['bytes'],
            'skipped_neighbors': window['skipped']})
        if source.media_type=='application/pdf':
            windows[-1].update(media_type='application/pdf',pages=[n for n,a,b in source.pages
                if a<window['end'] and b>window['start']])
    return {'version': VERSION, 'windows': windows, 'utf8_bytes': used, 'omitted_sources': omitted}
