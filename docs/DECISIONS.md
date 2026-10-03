# Architecture decisions

## ADR-032: patched runtime without Python installer tooling (3 October)

Keep the existing reviewed base and 96 application wheel pins. Add exact Debian
security versions for OpenSSL/PCRE2, then remove pip plus ensurepip from the runtime
filesystem. A separate named installer target retains build-time pip/hash checks.
This reduces runtime attack surface; it does not erase parent layers, make the
installer target safe for untrusted jobs, or freeze Debian repository availability.
Do not delete package metadata to hide scanner findings. Full rescan and runtime
absence/version probes verify the change; remaining findings stay open in TASK-023.

Windows subprocess timeout cleanup must remove the named Docker container before
closing inherited pipes, since killing Compose alone can wait for its child job.
A deliberate 120-second job now aborts and cleans up within a 20-second test budget.

## ADR-031: separate scan completion from security readiness (3 October)

The locked image now builds and passes offline restrictions. Its completed scan
still has open findings, including OS packages and pip bundled dependencies.
Track all records in IMAGE_SCAN_REVIEW.md and remediate through TASK-023 before
live execution. Do not treat a top-level package upgrade or disabled networking
as dismissal of a bundled-library advisory. Developer smoke jobs use unique names
and explicit cleanup on timeout; this does not replace the production supervisor.

## ADR-029: retain OKF as an optional extension (2 October)

User accepted keeping the recommendation: Open Knowledge Format may later support
portable linked notes and Obsidian exports. Keep keyword/vector retrieval and
Supabase as the search core; selected-source RAG chat remains deferred. Preserve
originals/citations and evaluate generated knowledge before indexing it as trusted
material. No OKF package or runtime added. Official format reference:
https://github.com/GoogleCloudPlatform/open-knowledge-format

## ADR-030: hash-locked extraction inputs, explicit review gates

Freeze the tested Linux/amd64 application package set as 96 exact wheel artifacts.
Pin the Python base by platform digest and bootstrap pip separately. Reject source
builds/unhashed dependencies during installation; don't assume a lock is proof of
security. Keep declared-license inventory and a repeatable advisory lookup that
fails visibly on feed errors/findings. NLTK's unpatched advisory and the incomplete
OS scan remain gates before live execution. Rebuild verification is blocked by
Docker storage health on 2 October. See services/worker/DEPENDENCY_REVIEW.md.

## 2 October proposals: ADR-026 through ADR-028

- ADR-026: propose a modular Python/FastAPI backend and trusted coordinator with
  separate restricted extraction. Retain Tauri/Supabase; recommend Cloud Run for
  later HTTP/batch hosting, subject to budget and egress feasibility. No service
  provisioned. Avoid additional brokers/GKE until measured requirements justify them.
- ADR-027: propose private Postgres jobs with atomic claims, leases, bounded retries
  and reconciliation. Source/version/job persistence is transactional; dispatch is
  recoverable. Requires concurrency, lease expiry, quota and deletion-race tests.
- ADR-028: propose separate keyword/semantic readiness and immutable generations.
  Activate only complete indexes, preserve old versions on failed refresh, and
  enforce tombstones at publication. Never substitute fake vectors for real AI.

These are planning defaults, not implementation claims. Details, tradeoffs,
dependencies and acceptance gates: [DELIVERY_PLAN.md](DELIVERY_PLAN.md).

Recorded 26 September 2026 from this project's existing decisions. Accepted means product/architecture direction, not implemented functionality.

| ADR | Decision | Reason / consequences | Status |
| --- | --- | --- | --- |
| 001 | Windows-first Tauri + React + TypeScript | User selected desktop; retain modern UI and controlled native boundary. Rust/toolchain and installer QA required. | Accepted |
| 002 | Supabase Free, Postgres + pgvector | User preference if free; auth, RLS and vectors together. Shared quotas/inactivity and online search are constraints. Chroma is contingency, not simultaneous backend. | Accepted |
| 003 | Local worker and inference | Original zero-recurring-cost approach; retained for history. | Superseded by 009 |
| 004 | Specialized model pipeline | EmbeddingGemma text, SigLIP visual, PaddleOCR scanned text, Qwen3.5 4B chat/vision. Runtime, versions, dimensions and quantization need measured selection. | Candidates accepted; benchmark pending |
| 005 | Separate embedding spaces + hybrid ranking | Text/image vectors are incompatible; keyword results preserve exact-name lookup. Group by original file. | Accepted |
| 006 | RAG first, no agentic file actions | Core need is reliable search and grounded answers. Model-directed tools/actions remain out of scope. | Accepted |
| 007 | User's anti-template design rules | Local fonts, solid surfaces, restrained interactions. GSAP blanket reveals and Lucide removed. Lenis optional, Motion selection, paused orb sample. | Implemented; visual QA pending |
| 008 | Structured delivery loop and Git checkpoints | User requested documented, small, tested, reviewed tasks through production. Adapt web examples to desktop, preserve the agreed stack. | Accepted |

Change a decision by adding an entry with alternatives, evidence and migration consequences. Do not silently replace accepted choices. MODEL_STRATEGY.md holds candidate research; resource/licensing notes live in DESIGN_AVOID_LIST.md.

## ADR-009: cloud AI, deployment deferred (27 September 2026)

User explicitly chose cloud-hosted AI to avoid end-user model downloads. Desktop
and Supabase Free stay; inference moves behind an authenticated cloud service.
Cloud provider, budget, runtime and queue are not selected and no paid resources
are authorized yet. Prior laptop-based model candidates need cloud cost/quality
evaluation. Shared provider credentials must never enter the desktop bundle.
Uploads/inference require ownership, quotas, retention disclosures and the
privacy release gates before real user content. Local SQLite job orchestration
is no longer the default target; durable cloud jobs will be designed later.

## ADR-010: bounded, transport-independent text contract (27 September 2026)

TASK-004 uses the Python standard library with strict UTF-8 input and exact
Unicode code-point source offsets. Preserve original text rather than normalize
away citation positions. Content hashes and versioned chunk IDs make retries
deterministic, but are never ownership credentials. Start with 64 KiB sources
and 1,024-character passages; actual tokenizer limits are TASK-005's gate.
Do not add an HTTP service, provider SDK or desktop bridge to test extraction.

## ADR-011: source-grounded retrieval development fixtures (27 September 2026)

Use original fictional TXT/Markdown documents with manually authored evidence
quotes. Derive exact offsets/acceptable overlapping chunks through TASK-004
rather than hand-maintaining chunk IDs. Fingerprint source content, questions
and labels; keep expected answers out of model inputs. Distinguish document
retrieval from evidence retrieval and absent-answer behavior. This authored
English development set is not independently reviewed or held out; broader
corpora and visual/OCR evaluation remain required before release claims.

## ADR-012: untuned lexical comparator and strict scoring (27 September 2026)

Use standard-library TF-IDF cosine retrieval as an inexpensive, reproducible
keyword baseline. No query-specific synonyms, stopwords, stemming or label access.
All positive-score chunks are ranked; score document recall after deduplicating
sources, but evidence recall on the first five chunks. Preserve absent queries
outside answerable metric denominators and do not equate candidates with answer
claims. Require complete rankings, valid source/chunk pairs and matching corpus
and processed-index hashes. This comparator is not production retrieval or proof
that embeddings are unnecessary. No provider dependency or paid resource added.

## ADR-013: saved-vector adapter before hosted inference (27 September 2026)

Decouple embedding production from offline comparison using a versioned export.
Validate consistent spaces and complete results before exact normalized cosine
ranking; compare it with TF-IDF and equal-weight RRF (constant 60). Use exhaustive
search for the small evaluation set so approximate-index behavior cannot obscure
model comparisons. Keep all similarity signs; do not invent an abstention
threshold. Tag synthetic vectors explicitly and never report their scores as
model quality. Real provider selection/token checks/usage accounting remain open.

## ADR-014: local quality command and manual CI (28 September 2026)

Use ESLint/TypeScript/Prettier plus the existing Python and UI tests/build in one
local command. Pin added development dependencies and commit the lockfile.
GitHub workflow is manual-dispatch only; authored but not run or pushed. Native
build/QA remains separate. User explicitly controls all pushes.

## ADR-015: bookmarks as library sources (28 September 2026)

User requested links including blogs, gaming sites and Instagram video URLs.
Save URL/notes first and enrich asynchronously; reuse the passage/vector pipeline.
Distinguish bookmark saving, available metadata, extracted page text and actual
video understanding. Inaccessible content remains a useful saved link. Build
synthetic extraction first, then owner-scoped persistence and restricted cloud
fetching. See BOOKMARKS.md for states, SSRF controls and release gates.

## ADR-016: search first and offline bookmark parsing (28 September 2026)

User deferred chat until later. Prioritize source ingestion and search; chat is
not a first-search release gate. Use a bounded standard-library HTML parser for
the initial offline contract, preserving metadata/text provenance and unavailable
states. This is a conservative heuristic, not universal article extraction or an
SSRF-safe fetcher. Real-world parser evaluation and cloud fetching remain pending.

## ADR-017: one documentation set for Obsidian and development (30 September 2026)

User requested ongoing Obsidian reference and documentation. Use the repository
as the existing vault, with PROJECT_HUB linking canonical documents. Add learning
notes, idea/session templates and a status-labelled canvas; avoid a duplicate
task ledger. Keep Obsidian settings/workspace local, preserve personal notes, and
do not enable services or community plugins. Update this knowledge base during
development checkpoints; app UI behavior remains unverified.

## ADR-018: Agent Reach-backed extraction adapters (30 September 2026)

User requested Agent Reach for saved links. Prefer selected upstream tools behind
explicit worker adapters; Gather owns durable bookmarks, passage provenance,
embeddings and retrieval. Toolkit setup is not a production fetching API.
Instagram's documented desktop Chrome-session path does not fit the current
cloud-worker plan. Public-page integration remains pending review and tests.
See docs/knowledge/AGENT_REACH.md for sources, limits and delivery gates.

## ADR-019: Crawl4AI and yt-dlp selected (30 September 2026)

User accepted the recommended stack: self-hosted Crawl4AI for webpages and yt-dlp
for supported video metadata/available subtitles. Supersedes ADR-018's core
Agent Reach preference; Agent Reach remains optional. Use explicit adapters and
preserve existing save/index/fetch security boundaries. No autonomous agent,
media download, transcription or visual video analysis is part of the initial
adapter. faster-whisper and chat remain deferred. Open-source licensing does
not make cloud operation free. Implementation order: TASK-018, TASK-019, TASK-017.

## ADR-020: archive historical prototype rather than discard it

On 30 September the user requested repository cleanup. Preserve the old PyQt,
Ollama, Chroma and agent experiments unchanged under legacy/ for reference, with
explicit unsupported status. Remove only unreferenced scaffold logos and OS
metadata. Preserve private data, environments, user notes and build dependencies.
Historical audit paths describe the old layout and remain historical evidence.

## ADR-021: field-specific versioned bookmark passages

TASK-018 reuses the existing text processor independently per URL, metadata,
notes and page-text field. Preserve exact field offsets and label evidence types;
version the whole extracted bookmark so retries remain stable and refresh changes
cannot share stale chunk IDs. IDs are not access control. TF-IDF remains an
offline test baseline, not claimed semantic search. No evaluation imports in the
worker. Crawl4AI/yt-dlp output normalization follows as TASK-019.

## ADR-022: normalize extractor output before enabling execution

Use pure Crawl4AI/yt-dlp output adapters and the existing passage builder. Preserve
Markdown without HTML reparsing; subtitle chunks retain overlapping timing cues,
language and automatic-caption provenance. Backend version/fetch time participate
in revision identity. Caller-supplied fixtures are not proof of live extraction.
Keep TASK-019 partial until isolated runners, pins and network checks exist.

## ADR-023: bounded caption parsing before downloads

Use a strict retrieval-oriented UTF-8 SRT/WebVTT subset, not a browser renderer.
Preserve overlapping/repeated cues and multiline text; strip display markup and
ignore VTT NOTE/STYLE/REGION blocks. Reject malformed cue blocks atomically.
Keep download/network execution separate and TASK-019 partial. Reference:
https://www.w3.org/TR/webvtt1/ (checked 30 September 2026).

## ADR-024: destination preflight is separate from network enforcement

Use an injected resolver and reject any non-public/mixed DNS answer, alternate
numeric host notation and non-web ports. Return immutable approved addresses.
The future transport must connect without resolving again and preserve TLS
hostname verification; browser subresources and redirects require the same
boundary. Do not equate DNS preflight tests with SSRF-safe live extraction.
Direct pins selected from PyPI: Crawl4AI 0.9.4 (Apache-2.0), yt-dlp 2026.8.19
(Unlicense). Transitive licences/lock and installed compatibility remain pending.

## ADR-025: network-disabled initial container

Use a dedicated extraction build context allowlist, non-root/read-only runtime,
resource limits, no host mounts and network_mode none for supplied-output jobs.
Do not enable networking until controlled egress and redirected/subresource
connections are enforced. Docker base tag and transitive pins are not yet locked
by digest. The current container is a preparatory artifact, not verified isolation.
