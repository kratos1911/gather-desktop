# Offline bookmark passages

`prepare_bookmark(source_id, url, html=None, notes="")` accepts synthetic or
caller-supplied HTML using the existing bounded extractor. No fetching, database,
model or desktop integration is performed. Source IDs must be 1-64 ASCII letters,
digits, underscores or hyphens; they are not authorization credentials.

Fields remain separate: URL, user notes, page text and individual metadata fields.
The existing TXT processor chunks each field. Offsets are Unicode code points in
the exact returned field string, not raw HTML. Chunk IDs include source identity,
full bookmark revision, field and text-chunk identity. A changed revision replaces
the entire passage set in future storage; this module does not perform replacement.

Extraction limits remain 64 KiB UTF-8 HTML, 256 nesting levels and 8192 note
characters. Each nonempty field must pass the text processor's limits/control
checks; any failure raises a content-free ValueError code, returning no partial
result. URL/notes survive an unavailable extraction outcome; metadata-only video
links never produce invented transcript passages.

Status is `passages_prepared`, with `semantic_ready: false`. Future indexing must
enforce ownership, commit atomically by version and generate real embeddings.
The offline TF-IDF evaluation consumes the resulting `id`/`chunks` structure;
production worker code does not import evaluation scripts. Seven tests check
stable retries, refresh, source separation, offsets, fallback and late-page hits.

Crawl4AI Markdown and yt-dlp subtitles need separate adapters in TASK-019. This
HTML API must not pretend those outputs are HTML or discard subtitle timestamps.
