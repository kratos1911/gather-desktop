# Selected link extraction stack

Accepted by the user on 30 September 2026. Supersedes Agent Reach as the preferred
core toolkit (ADR-018). Return to [[docs/PROJECT_HUB]] and [[docs/BOOKMARKS]].

| Source | Selected tool | Initial scope |
| --- | --- | --- |
| Public webpage or article | Self-hosted Crawl4AI | Readable text/Markdown and metadata. |
| Supported video link | yt-dlp | Metadata and available subtitles only; no default media download. |
| Accessible speech without subtitles | faster-whisper, deferred | Later transcription after a separately tested media-processing task. |
| Private, blocked or unsupported page | Saved URL and user notes | Honest unavailable/metadata-only status; no promise of universal extraction. |

Agent Reach remains an optional future helper, not a required dependency.
Software is open source; cloud compute, storage and bandwidth are not guaranteed
free. No hosted paid crawler or proxy service is selected.

## Flow

Save bookmark -> bounded extraction job -> choose source adapter -> normalize
text/metadata/subtitle evidence -> versioned passages -> cloud embeddings ->
owner-scoped Supabase index -> search results with source references.

Routing is deterministic application logic. No autonomous agent is needed to
choose shell commands or navigate accounts. Unsupported video sites must fall
back honestly, not claim their page title is a transcript.

## Implementation gates

TASK-018 connects extracted bookmark fields to passages and offline keyword
retrieval first. TASK-019 then adds the selected extraction adapters with pinned
versions, licenses and mocked output tests. TASK-017 connects the durable workflow.

- Keep fetched page text, user notes and subtitles labelled separately. Retain
  source URL, retrieval time, backend version and subtitle timestamps/language.
- Crawl4AI Markdown/text does not go through the raw-HTML parser again.
- Bound time, content size, concurrent browsers, retries and supported domains.
- Enforce network restrictions for redirects and browser subresources as well
  as the original URL; a URL validator alone is insufficient for SSRF prevention.
- Invoke controlled libraries/argument lists; never interpolate URLs into shell
  commands. Do not import personal browser sessions or shared account cookies.
- Version refreshes and preserve bookmarks when extraction fails. Mark semantic
  readiness only after actual embeddings and index writes complete.
- Test public access and site compatibility before support claims. Real-world
  extraction, browser/native QA, Supabase and model integration remain pending.

Video frame analysis, media transcription and document chat remain deferred.
Available subtitle indexing is distinct from visual understanding of video.

## Upstream references

Reviewed during the recommendation on 30 September:
- [Crawl4AI](https://github.com/unclecode/crawl4ai)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [yt-dlp site support limitations](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)

Selection checkpoint (30 September): selected, not installed or connected. No network scraping or paid
provisioning is implied by this selection.

## Output-adapter checkpoint

TASK-019 is partial. Pure Crawl4AI dictionary and yt-dlp metadata/normalized-cue
adapters feed the shared passage pipeline. See
[contract](../../services/worker/EXTRACTION_ADAPTERS.md). Eight synthetic tests
pass; the tools themselves are not installed or executed. Runners, dependency
pins, subtitle-file parsing and live compatibility checks remain next.

## Current container checkpoint, 1 October

Crawl4AI 0.9.4 and yt-dlp 2026.8.19 are installed in the built Docker image.
The bounded runner consumes supplied results; it does not invoke these tools yet.
SRT/WebVTT parsing and public-address preflight policy have offline tests.
Container smoke checks verify selected runtime restrictions with networking fully
disabled. Public-only egress, live invocation, Chromium installation and locked
transitive dependencies/base image are still pending. See the runner guide and
TASK-019 for evidence. No real semantic retrieval demonstrated.


## Current boundary checkpoint, 3 October

Base/wheel locks and available security patches are verified; the rescan retains
31 records (four high). Plain-HTTP transport and offline Docker supervision pass
controlled tests. Neither invokes Crawl4AI/yt-dlp or fetches real user links.
Whole-broker DNS deadlines, browser/tool egress and live compatibility remain open.
See [[services/worker/SUPERVISION]]; earlier checkpoints above are historical.
