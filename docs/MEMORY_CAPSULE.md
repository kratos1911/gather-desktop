# Gather — project memory capsule and resume evidence

Snapshot: 22 October 2026. Verified code checkpoint: e9ed325 on
codex/durable-ingestion-jobs. This is a handoff snapshot, not a replacement for
canonical project notes. Later repository evidence takes precedence.

## 1. Product and current truth

Gather is a Windows desktop personal knowledge library for finding saved material
using natural-language queries. The goal is to retrieve actual source passages
with references, even when the user cannot remember the filename or exact words.

First usable flow: import TXT/Markdown -> process -> persist -> semantic search ->
open exact source/version -> delete, with authenticated ownership throughout.

Current maturity: working backend prototype with a successful hosted operator
pilot; styled desktop preview still uses sample data. The private embedding model
is deployed. The application API adapter exists but has no runnable listener or
verified live HTTP integration yet. This is not a released, fully connected app.
There is no measured production user count, uptime, revenue or general-scale SLA.

Planned broader scope: PDF, DOCX, PPTX, bookmarks/webpages, images/screenshots/OCR.
Selected-source chat is explicitly deferred until search is useful and reliable.
Do not claim universal website/video extraction or completed multimodal support.

## 2. Stack and responsibilities

| Layer | Technology | Actual status |
| --- | --- | --- |
| Desktop | React, TypeScript, Vite, Tauri | Sample library/reader and Windows shell implemented |
| Visual system | Bundled Manrope, system document fonts, reusable CSS tokens | Forest/citron/coral redesign implemented; full native QA remains |
| Backend | Python modules; internal dependency-free ASGI application adapter | Processing/retrieval/jobs implemented; server lifecycle pending |
| Inference serving | FastAPI/Uvicorn, bounded CPU runtime, Docker | Private Google Cloud Run service deployed |
| Embedding model | Qwen/Qwen3-Embedding-0.6B | Pinned revision, 512-dimensional vectors |
| Authentication | Supabase Auth | Real hosted pilot sessions verified |
| Persistence | Supabase PostgreSQL + pgvector | Migrations applied; hosted text pilot passed |
| Original storage | Private database original handoff for current bounded text slice | General object-storage adapter pending; Cloudflare R2 selected target |
| Retrieval evaluation | TF-IDF baseline, vector ranking/RRF experiments, frozen fixtures | Evaluation tools exist; not a completed desktop hybrid-search feature |
| Extraction | Python parsing; Crawl4AI and yt-dlp selected adapters | Offline/controlled tests exist; live product integration pending |
| Version control | Git/GitHub | Local checkpoints; push only on explicit request |

Architecture today:

    Desktop preview (sample data; not connected)
                     |
              planned connection
                     v
    Application ASGI adapter (implemented; not listening/deployed)
                     |
           fresh authenticated LibrarySession
                /                    \
     Supabase Auth + RPC          trusted admission repository
             |                           |
      published search/open       source + immutable version + job
      status/delete                      |
             |                    existing ingestion coordinator
             |                    claim -> parse -> chunk -> embed
             |                           |
             |                  private stage -> atomic publication
             |                           |
             +---------- Supabase PostgreSQL / pgvector
                                         ^
                                         |
                           private CPU inference API
                           Google Cloud Run, Mumbai

Supabase pilot region: Sydney, retained by explicit user decision. Cross-region
latency was observed; this is an accepted pilot tradeoff, not optimized production
placement. End users will not need model weights, Docker or a local AI runtime.

## 3. Work completed

### Planning and development discipline

- Established PRD, architecture, design, task tracking, decisions, testing,
  security/privacy gates and canonical progress notes.
- Added Obsidian-compatible project hub, knowledge notes and source-flow canvas.
- Defined small milestones and explicit implemented/tested/planned distinctions.
- Added desktop/CLI collaboration guidance with one writer and scoped handoffs.
- Added Python and desktop runtime-selection scripts after environment issues.

### Desktop preview

- Built React/TypeScript library, filtering/search interactions, source reader,
  navigation and explanatory preview states inside a Tauri shell.
- Redesigned typography, surfaces, navigation, selection and focus states using
  a cohesive color system and locally bundled font provenance.
- Preserved explicit sample-data labeling. Real authentication/import/search is
  not connected to desktop controls yet.

### Text processing and retrieval

- Implemented bounded TXT/Markdown byte validation and deterministic extraction.
- Preserved source hashes, parser/chunker versions, text offsets and citations.
- Built TF-IDF baseline and versioned retrieval evaluation fixtures.
- Implemented a pinned embedding client and real CPU model evaluation tooling.
- Added token-aware passage preparation, model/dimension compatibility checks,
  vector validation and bounded same-source context assembly.
- Context assembly preserves ownership/version boundaries and exact source spans;
  it expands only within defined resource limits.
- Main evaluation retrieval passed, but split-context and multi-part evidence
  coverage remain limitations. Do not imply perfect retrieval or broad accuracy.

### Reliable ingestion and persistence

- Added source/version ownership schema and database authorization boundaries.
- Implemented durable jobs with queued/processing/ready/failed outcomes, leases,
  bounded claims, retries and stale-worker fencing.
- Added idempotent submission and private immutable-original handoff.
- Validated actual content bytes, type, size and SHA-256 against source versions.
- Added private passage/vector staging and completeness validation.
- Implemented atomic publication: only a complete valid version becomes searchable.
- Kept previous published versions available while replacements are processed.
- Prevented late/stale workers from publishing deleted or superseded versions.
- Implemented immediate deletion tombstones and separate physical cleanup.
- Connected parser, chunker, embedding provider, lease maintenance, staging and
  publication through a trusted ingestion coordinator.

### Authentication, transport and security

- Added LibrarySession, deriving identity from validated Supabase Auth sessions.
- Reused the same user bearer for ownership-enforced PostgREST operations.
- Built restricted admission/worker database roles and bounded Psycopg transport.
- Enforced TLS certificate/hostname verification for hosted database connections.
- Added fixed service routes, bounded request/response sizes, cancellation,
  deadlines and safe error codes without exposing provider/database details.
- Implemented managed Google service identity validation and private Cloud Run
  invocation using a dedicated caller service account.
- Added operator-only Windows current-user DPAPI credential storage. This is not
  the final cloud secret distribution mechanism or a desktop credential bundle.
- Worked on dependency/license notices, vulnerability scans and a zlib backport;
  scanner findings/release gates remain documented, not universally cleared.

### Cloud deployment and hosted pilot

- Built and tested a model-bearing CPU container with pinned dependencies/model.
- Uploaded an image by digest and deployed private inference on Cloud Run.
- Pilot configuration: 2 vCPU, 5 GiB RAM, concurrency 1, maximum 1 instance;
  normal minimum 0. No GPU required for this chosen pilot model/configuration.
- Verified unauthenticated inference access is rejected; an authorized request
  returned the pinned model/revision and a 512-dimensional vector.
- Applied seven Supabase migrations and verified restricted hosted DB logins.
- Created two operator-managed synthetic Auth accounts; public signup stays off.
- Completed a hosted flow using real Auth, PostgreSQL and cloud embeddings:
  import -> ready -> semantic search -> exact text opening -> deletion hiding.
- Tested ownership isolation within that pilot. Final physical cleanup=true was
  reported by the operator after the run; the saved receipt predates cleanup.
- Added scoped temporary warm capacity and finally-based restoration to min0,
  plus safe receipts and explicit cleanup/restart guards after failures.

### Latest checkpoint: application API adapter

Implemented services/worker/library_api.py with five POST routes:

- /v1/import
- /v1/search
- /v1/status
- /v1/open
- /v1/delete

The adapter creates a fresh per-bearer session, rejects owner overrides and unknown
fields, validates bounded JSON/base64 text, returns fixed safe errors, and uses
no-store responses. Import acknowledges queued work rather than claiming ready.
It cancels on timeout/disconnect and retains its single-flight slot until the
underlying operation actually returns. It does not start a worker inline.

Limits: original 64 KiB; request JSON 96 KiB; response 512 KiB; body read 5 seconds;
response wait 30 seconds. Existing model/SQL/database limits are unchanged.
One active operation per adapter instance is not a distributed per-user rate limit.

## 4. Evidence and what it does NOT prove

- Hosted pilot: passed=true, stage=complete, job state=ready; two real model
  requests and two compatible query-vector response replays on one synthetic TXT.
  This proves the bounded hosted path, not broad semantic accuracy or load capacity.
- Initial authorized cloud query example: 512-vector response in 1.06 seconds.
  This is one observed request, not p95/p99 or a general latency guarantee.
- Model-bearing local release test: four real HTTP model requests; startup18.55s,
  peak4.09GiB. Earlier container smoke: startup15.781s, short calls0.593-0.742s,
  peak3.87GiB. These are different runs, not directly comparable cloud benchmarks.
- Paired chunk evaluation checkpoint: 178 model requests, 70 checks and frontend
  build completed. Known split-context/multi-part coverage gaps remain.
- Latest API checkpoint: 17 focused synthetic API/session tests pass; desktop
  production build passes. Tests use ASGI messages and simulated external services,
  not live application HTTP sockets or a newly deployed application service.
- Security scans still have documented OS findings. Do not say vulnerability-free,
  formally compliant, penetration-tested or production-secure without new evidence.

Key evidence/docs: TASKS.md; docs/HOSTED_FLOW_PILOT.md; docs/LIBRARY_API.md;
docs/CHUNK_RETRIEVAL_RESULTS.md; services/inference/PROFILE_RESULTS.md;
tests/inference/results/; output/hosted-pilot/receipt.json (ignored local evidence).

## 5. Next milestones, in order

1. Runnable local application API and worker lifecycle.
   Compose trusted configuration/secrets with existing modules, establish bounded
   worker execution/shutdown, and verify actual HTTP requests end to end. Reuse
   synthetic vectors first; no new full benchmark is needed for HTTP plumbing.
2. Connect the desktop's first real text flow.
   Add real session handling and native TXT/Markdown selection, import/status,
   search results, exact source opening and deletion. Preserve sample mode as an
   explicit separate state; test two-user isolation and error recovery.
3. Controlled application hosting and release gates.
   Add server-side secret management, caller/IAM policy, verified-owner rate limits,
   deployment-wide capacity, TLS/origin rules, budget monitoring and worker trigger.
   Complete applicable privacy/disclosure gates before personal uploads. Obtain
   explicit approval for new paid provisioning; keep inference scale-to-zero.
4. Small consenting-user pilot and quality measurement.
   Measure real workflow failures and retrieval coverage; address split-context,
   multi-part passages, cold starts and cross-region latency. Test native installer,
   keyboard access, narrow windows, offline/error states and full cleanup.
5. Broaden supported content incrementally.
   Native-text PDF/DOCX/PPTX; durable bookmarks plus restricted live extraction;
   images/OCR as a separately evaluated retrieval space; object-storage adapter.
   Add hybrid ranking only with measured value and honest UI labeling.
6. Selected-source chat later.
   Ground answers in retrieved evidence with citations and strict source isolation.
   Chat/generative question answering is not implemented today.

## 6. Important lessons and decisions

- Authentication proves validated identity; authorization decides resource access.
  Client-supplied user IDs must never select privileged owner context.
- Search and indexed passages must use compatible pinned embedding spaces.
- Durable idempotency handles retries; atomic publication hides partial work.
- Lease fencing prevents old workers from restoring deleted/replaced content.
- A timeout/disconnect does not itself prove remote compute stopped or DB rollback.
- Cold-start readiness and inference computation deadlines are different budgets.
- Repeated short database handshakes failed across regions. Explicit pilot-only
  connect10/operation15 allowances were approved; production defaults remain3/5.
- Synchronous cloud scaling waited too long locally. Separate accepted async update
  from generation/Ready observation inside the existing startup budget.
- Temporary warm instances can bill while idle. Restore minimum zero on exit and
  expose rollback uncertainty; this is not an absolute spend cap.
- Reuse frozen fixtures, saved compatible vectors and prior evidence. Do not keep
  loading models for application/DB-only changes or retry unchanged RAM failures.

## 7. Handoff rules for another coding model

Repository: D:\Ollama\Original_Code\AI-Agent-Code-Generator-main.
Start with branch/HEAD/status. Read AGENTS.md and required canonical notes once.
Current truth: top of MEMORY.md and newest evidence; many older notes are historical.
Preserve pre-existing untracked error.txt and output.txt. One writer/agent by default.
Use scripts/python.ps1 for light Python checks and scripts/desktop.ps1 for frontend.
Keep artifacts on D:. Never push without explicit user permission. Protect unrelated
API containers and Intrixshield; never use its project/account for Gather.
No model loads or Docker runs for routine HTTP changes. No blind cloud retries.
Ask before paid/destructive/protected-workload actions. Keep secrets out of chat,
logs, repository and desktop. Some previously exposed credentials still require
rotation before broader release; the user explicitly deferred that earlier.
Quiz the user briefly before each major milestone, with at most 1-2 important
AI Engineer interview questions and concise corrections, without prolonged followups.

Resume context: AI-assisted development. Claim ownership of design, implementation,
verification and decisions you can personally explain; do not imply sole manual
authorship, production scale, perfect security or features that remain planned.

## 8. Resume-ready wording

Gather — Semantic Document Search | React, TypeScript, Tauri, Python,
PostgreSQL/pgvector, Supabase, Docker, Google Cloud Run

- Built a personal knowledge-search backend that processes TXT/Markdown into
  versioned passages and retrieves cited source content using cloud-hosted Qwen
  embeddings and PostgreSQL/pgvector.
- Implemented durable ingestion jobs, idempotent submission, lease-based worker
  coordination and atomic index publication to handle retries, replacements and
  deletion without exposing incomplete processing results.
- Deployed a private CPU inference service on Google Cloud Run and validated a
  hosted import-search-open-delete pilot with real authentication and ownership
  isolation across two synthetic test accounts.
- Developed a React/Tauri desktop preview and a bounded five-route Python ASGI
  API adapter; verified the latest API/session change with 17 focused tests.

Short interview introduction:
"Gather is my AI-assisted semantic-search project for saved documents. I built
and verified the backend ingestion, model-serving and retrieval path, including
ownership enforcement and safe retries. The embedding model runs privately on
Cloud Run, with Supabase Auth and pgvector. A hosted text pilot works; I am now
connecting the application server and desktop so users can complete that flow
through the UI."

Avoid claiming now: complete production app; large user base; production RAG
chatbot; full multimodal search; universal scraping; achieved p95<2s at10k chunks;
zero operating cost; eliminated all vulnerabilities; public release completed.
