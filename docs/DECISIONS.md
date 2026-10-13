# Architecture decisions

## ADR-040: persistent inference behind a killable process (12 October)

Keep the loaded model in a separate reusable process. A timed-out thread cannot
reliably interrupt native model work, so timeout handling terminates and reaps
the child. Reject concurrent requests rather than accumulating a queue; require
an explicit restart after failure. This is a private serving primitive, not an
HTTP API, OS resource sandbox or Cloud Run deployment. Use the frozen Qwen prompt,
revision and 512-dimensional space; do not replace the benchmark protocol.

Fourteen synthetic tests pass. The real host smoke passed on 13 October after
RAM became available; container packaging waits for verified Docker storage on D:. User confirmed
Gemma terms accepted and will authenticate locally; no token requested in chat.

## ADR-039: freeze fresh cases and preserve retrieval failures (12 October)

Advance TASK-005 with text-v2 rather than tune v1. Author 40 fictional sources
and 64 questions across eight new domains, including archived/current and related
records, eight late passages and eight absent cases. Freeze sources and relevance
quotes with a canonical hash before inference. Validate changes and reject mixed
corpus outputs. Keep v1 locations and twelve recorded artifact hashes intact.

Use unchanged Qwen revision, prompt, chunker, float32, exact cosine and RRF k=60.
512 dimensions was the primary candidate before results, with >=0.90 thresholds
for document/evidence Recall@5 and MRR. It passes (1.0/0.9911/0.9613). Advance it
to a bounded CPU serving-container experiment, not a final production selection.
1,024 has higher MRR and 512 better evidence recall; small samples do not prove
a universal optimum. RRF lowers overall MRR, so it remains a comparator.

Preserve the five nonperfect 512-dense cases and absent-neighbor behavior. Do not
edit labels or tune prompts to erase them. Exact identifiers, temporal distinctions
and multi-part evidence coverage need separate retrieval work. These examples
were authored by the assistant after v1, not independently labelled/blind. No
Cloud Run deployment, cost inference, additional model download or push occurred.

## ADR-038: measure self-hosted CPU embeddings on D: before deployment (10 October)

Latest user choices supersede provider-deferred notes: Google Cloud Run,
self-hosted CPU AI first, R2 originals, Supabase Free Auth/Postgres/pgvector.
The cloud account exists; no application deployment is verified by this task.
R2 is object storage, not a replacement vector database. Per-user/global storage
admission and request/compute quotas remain to be implemented; budget alerts
are not spending caps. Existing local Supabase Storage tests do not verify R2.

User permits local model downloads/testing on D: because C: has little space.
Use an isolated D: venv/cache/temp/output and CPU-only wheel, pinned model
safetensors, no remote model code, anonymous download and offline inference.
Model artifacts are ignored by Git. This developer benchmark does not change the
cloud deployment requirement or require end users to download weights.

User explicitly chose Qwen first; EmbeddingGemma terms have not been accepted.
Keep that candidate pending without bypassing the gate. Keep chat deferred and
require a separate visual corpus for SigLIP/OCR rather than scoring them as text
models. Reuse text-v1 and the existing strict cosine/RRF scorer, with labels
excluded from inference. Reject token overflow before model execution.

Measured all three Qwen dimensions on two/four threads. 512 dimensions has the
best development-set MRR (0.9857), but no production winner is selected from
35 answerable examples. Fixed RRF lowered ranking quality versus dense; expand
the evaluation before choosing fusion. Laptop timing is not Cloud Run billing
or service capacity. See CPU_BENCHMARK.md for reproducible evidence and limits.

## ADR-037: verify core APIs and order Storage cleanup before SQL (9 October)

Use real Auth, PostgREST and Storage images with a disposable PostgreSQL database
to move beyond identity shims. Auth/Storage install their own schemas; the harness
supplies test roles and exercises real JWTs. Image digests are pinned. Only the
gateway has an explicit loopback port; database/file data lives in bounded tmpfs.
This verifies core API behavior, not complete hosted/CLI/default-grant parity.

The CLI's recommended network-level loopback setting still published on all
interfaces in this environment. Stop that stack and use explicit Compose port
bindings verified before fixtures. Do not change Docker's global settings or
unrelated workloads. The CLI is not required by the final test runner.

Create a private, bounded original-file bucket with owner/live-source read policy.
Keep client upload/overwrite/delete denied. Remove bytes via the Storage API;
SQL finalization refuses remaining source-prefix object metadata. A failed or
interrupted external removal retains the cleanup request and slot charge.
31 API checks pass, including two-owner isolation and retry after external removal.
No background worker is implemented. In-flight privileged uploads, signed URLs,
orphan reconciliation and byte/rate budgets need explicit follow-up gates.

## ADR-036: serialize source quotas and preserve deletion receipts (9 October)

Use per-owner quota row locks to serialize saves and cleanup. Store source,
receipt and slot charge atomically; derive owner from auth.uid() and restrict
security-definer functions with an empty search path and explicit grants.
No default allowance: trusted administration must configure it. This is a
source-count quota only; byte/rate/inference budgets remain future gates.

Retain minimal idempotency receipts after database cleanup so a repeated save
cannot resurrect a deleted source. Reusing the key with changed input fails.
Retention/account erasure needs a future explicit policy. Deletes create durable
cleanup requests and tombstones together, retaining quota until cleanup commits.
Database-only cleanup has no worker grant and must not finalize future Storage
assets before verified external deletion. Version writes lock the live parent.
45 SQL assertions and four concurrency scenarios pass on PostgreSQL with a
test-only Auth contract; no full Supabase/desktop integration claim.

## ADR-035: verify source ownership before enabling ingestion (8 October)

Start TASK-021 with Supabase-targeted SQL migrations and a disposable PostgreSQL
17 harness. The system drive has about 2.7 GB free; avoid the full Supabase stack
and leave unrelated Docker services untouched. Test-only auth.users/auth.uid
contracts permit actual role/RLS checks but do not prove JWT, Auth or Storage.
Pin the test image by digest, use bounded tmpfs/no network/no host ports, clean up
only the generated test container. No application data is retained.

Clients may read their records and edit title/notes. Creation, ownership,
versions and deletion are not client-writable. Composite owner/source foreign
keys stop inconsistent privileged writes. Tombstones hide dependent versions;
cleanup and quota transactions must precede enabling lifecycle APIs. Do not add
vector dimensions or ready states before model/publication contracts exist.

## ADR-034: supervise the entire fetch and pass bytes to offline parsing (8 October)

Use one fixed Python child per fetch so the parent deadline also covers blocked
OS DNS and TLS/connect operations. Bound both streams and the decoded result,
allowlist inherited environment, kill/reap on timeout/cancel, and never publish
partial or still-running output. No arbitrary child code comes from job data.
The host process boundary is lifecycle control, not a production OS sandbox.

Add an explicit http-page adapter instead of relabelling raw HTML as Crawl4AI
output. Preserve URL, fetch time, redirects, raw-body hash and actual parser
provenance; plaintext remains literal. Pass bytes into the existing network-none
Docker runner. Failures leave persistence decisions to the future coordinator;
no save/index or semantic readiness is claimed. Browser/tool egress, durable job
recovery, external compatibility and open dependency findings remain release gates.

## ADR-033: separate restricted fetching from offline parsing (3 October)

Introduce a small backend-only page transport that approves each DNS/redirect
hop, dials numeric approved addresses and preserves TLS hostname checks. Do not
forward cookies or execute page scripts/assets; reject compressed/unbounded data.
Known NAT64 ranges are denied to avoid translating a public-looking IPv6 address
into private IPv4. Test injection is trusted code, never a request option.

Keep the supplied-output parser on network none behind DockerJobRunner, with
fixed operator-selected image digest/entrypoint, bounded I/O and resources,
timeout/cancellation and exact-container cleanup. No Docker socket in the worker.
Plain HTTP transport is not browser egress enforcement, and socket deadlines do
not bound OS DNS. TASK-019B remains partial until a whole-broker process deadline
and integration are tested. Durable crash cleanup and global quotas remain later
coordinator responsibilities. See services/worker/SUPERVISION.md.

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
