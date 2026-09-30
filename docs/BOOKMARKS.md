# Links and bookmarks

Requested 28 September 2026. Offline parsing implemented; live integration pending. Chat deferred until search works.

## Flow

Paste URL -> validate -> save private bookmark -> background enrichment ->
extract available text -> chunk/embed -> search -> open source or original page.
Optional user title/notes make inaccessible links useful. Results distinguish
user notes, metadata, article text and supported transcripts as evidence types.

Separate saving from indexing: saved, queued, fetching, metadata-only, extracted,
indexing, searchable, extraction-unavailable and failed. Show a reason and
retry/edit/remove action. Failed enrichment never discards the saved bookmark.
URL/title/notes remain eligible for ordinary keyword search once persistence is
connected, even when page text cannot be extracted.

## Techniques and coverage

30 September final selection: Crawl4AI for webpages, yt-dlp for supported video
metadata and available subtitles. See [[docs/knowledge/EXTRACTION_STACK]].
Agent Reach is optional; live integration remains pending. Extractors do not
replace Gather persistence, chunking or semantic search.

Implemented offline API: `extract_bookmark(url, html=None, notes="")` in
services/worker/bookmarks.py. HTML must be UTF-8 bytes, at most 64 KiB; nesting
is capped at 256 and notes at 8192 characters. Ten synthetic tests pass.
The heuristic prefers main/article text; body fallback can include boilerplate.
It removes selected non-content elements, not all advertising or CSS-hidden text.
Extracted strings must be rendered as text, never inserted as HTML. Paragraph
offsets refer to normalized extracted text, not the original HTML. Source hash
and parser version support future indexing; no passages are indexed yet.
URL validation does not resolve DNS and is not sufficient authorization to fetch.

- URL parsing and conservative normalization for owner-scoped duplicate handling.
  Retain the original URL; do not indiscriminately strip queries/fragments.
- Metadata extraction for available title, description, site name and author.
  Missing fields remain missing; no AI-generated guesses.
- Article extraction separates readable text from navigation and advertising.
  Preserve headings/paragraph references; treat HTML as data, never executable UI.
- Existing chunking, embeddings and hybrid retrieval index the extracted text.
  Selected-source chat cites the actual saved evidence and its fetch time.

Blogs, gaming sites and other public pages share this path. Social/video links
such as Instagram URLs are saved even if only their URL or metadata is accessible.
Index captions/transcripts only when legitimately available through a supported
adapter, labelled with provenance. Video downloading, frame analysis and speech
transcription remain the separately scoped video/audio phase. A title alone does
not mean the video was understood. No login/paywall bypass or cookie harvesting.
Dynamic/private/blocked pages get honest unavailable or metadata-only states;
universal website parsing is not promised.

## Data and lifecycle

Use a common library-source identity for files and bookmarks during schema design.
Store owner/source ID/type, original and normalized URL, final fetched URL,
user title/notes, extracted metadata/text, fetch time, parser version, content
hash and processing status/error. Keep user-edited fields separate from extracted
ones. Never use a page's canonical URL to merge records automatically.

Explicit refresh creates a new content version, switches searchable chunks only
after complete indexing, then retires stale derivatives. Pages can change or
disappear; the reader shows when its snapshot was fetched. Deletion immediately
removes search visibility and eventually cleans every owned derivative.

## Security and privacy gates before network access

Authenticate and enforce quotas. Bound redirects, response/decompressed size,
timeouts and content types. Prevent server-side request forgery: reject local,
private, link-local, reserved and cloud-metadata destinations; recheck DNS and
every redirect, with connection/egress enforcement against DNS rebinding. A URL
regex alone is not sufficient. Accept public HTTP(S), never file/data/javascript
schemes or embedded credentials. No user-cookie/header forwarding or unvalidated
thumbnail/embedded-resource fetching. Avoid sensitive URL query strings in logs.

Disclose destination-site contact and cloud processing/storage. Review provider
retention, site access/robots rules, copyright and parser licenses before live
enrichment. PRIVACY_RELEASE_AUDIT.md's operator/auth/contact gates still apply.

## Delivery tasks

TASK-016: synthetic URL/HTML processing contract; test metadata/article extraction,
source provenance, malformed/unsafe URLs, malicious HTML, missing fields,
unsupported/oversized content and fallback. No real fetch/account required.

TASK-017: save-link UI and private persistence, restricted fetcher, durable jobs,
semantic indexing and deletion. Chat is deferred. Test two-user isolation, redirected blocked
addresses, DNS rebinding, retries/restart, duplicates, refresh and disappearing
pages. Add bookmark evaluation in a new version; preserve frozen text-v1.

No desktop bookmark input, persistence, fetcher or semantic bookmark results are implemented
by this specification. Provider selection and deployment remain deferred.

## TASK-018 checkpoint

Offline passage preparation is implemented; see
[worker contract](../services/worker/BOOKMARK_PASSAGES.md). Seven tests cover
provenance and TF-IDF retrieval. Passages are not stored or semantically indexed;
Crawl4AI/yt-dlp output adapters are next. Earlier task descriptions above describe
the delivery plan, not additional live functionality.
