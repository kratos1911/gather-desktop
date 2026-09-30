# Extraction output adapters

TASK-019 partial: pure output conversion, not executable crawler integration.
`crawl4ai_passages` accepts a supplied CrawlResult dictionary with success, HTTP
status, URL, metadata and Markdown (string or raw_markdown dictionary). Failed
HTTP responses do not contribute page text. It preserves Markdown rather than
feeding it through HTML parsing. `ytdlp_passages` accepts single-video metadata
and optional normalized subtitle cues supplied separately by the caller.

Cues are `{start: seconds, end: seconds, text: string}`; starts must be ordered,
times finite/nonnegative and ends after starts. Overlapping cues are allowed.
Language and automatic-caption provenance accompany each subtitle passage.
Offsets refer to the joined transcript; each chunk carries overlapping cue spans.
This does not parse VTT/SRT, fetch subtitle URLs or analyze video frames.

Both require an explicit backend version and timezone-aware retrieval timestamp,
retained in output and revision identity. These are caller assertions, not proof
of an actual fetch. Tests label the version fixture-v1. Successful output remains
passages_prepared and semantic_ready=false. Source IDs do not enforce ownership.

Limits: page/transcript UTF-8 text 64 KiB; 1000 subtitle cues; 8 KiB per cue/video
metadata field, 4 KiB per webpage metadata field, 8 KiB notes. Invalid types,
controls, oversized text and unsafe literal URLs are rejected with generic codes.
Upstream errors, headers, cookies, arbitrary metadata and download URLs are not
copied. Input dictionaries must be created from bounded transport by the future
runner; this module is not an HTTP or DNS/redirect/subresource security boundary.

Eight synthetic tests plus existing passage tests cover failures, Markdown,
redirect provenance, metadata-only results, cues, limits and revision changes.
No Crawl4AI/yt-dlp installation or real compatibility test has occurred. Dependency
pinning/license review, isolated execution, network enforcement, bounded subtitle
downloads/parsing and approved public-site tests are still required in TASK-019.
Self-hosted execution will contact destination sites; any third-party reader or
proxy requires an explicit recorded data-recipient decision before use.

Protocol references checked 30 September 2026:
- https://docs.crawl4ai.com/api/crawl-result/
- https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/common.py
