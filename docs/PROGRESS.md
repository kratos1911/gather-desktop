# Rebuild progress

## 2026-09-26 — foundation

Completed:
- Inspected the existing PyQt/Python implementation.
- Confirmed user direction: Windows-first desktop, Tauri + React, Supabase vectors, semantic search first and document chat second.
- Wrote project blueprint, delivery gates and interface/motion direction.
- Identified original bugs: first-chunk-only indexing in the desktop path, moving source files, inconsistent metadata, incomplete persistence and stale vectors after deletion.

Environment findings:
- This directory is not currently a Git repository.
- Node reports v22.7.0.
- The currently resolved npm command fails because its npm-cli.js target is missing.
- Rust is not available on PATH or at the standard user cargo location checked.
- Visual Studio Installer exists; the required C++ workload has not been verified.
- Supabase connectivity, credentials and project configuration have not been tested.

No existing source files, original documents, legacy databases or environment secrets were modified. No cloud resources were created and no personal files were uploaded.

Next: resolve the desktop development toolchain, scaffold apps/desktop and build the labelled interactive prototype. In parallel with implementation work, settle the hosting budget and model strategy before introducing a paid dependency. A working Windows installer remains unverified until Tauri prerequisites are available.

Budget update: user requires free operation. Keep Supabase Free for a bounded initial release; revise processing to a bundled local worker and local models. No paid hosting or inference dependency. Verify shared quotas, local hardware requirements and Supabase inactivity behavior before release.

Model research: clarified Gallery-inspired multimodal scope; added MODEL_STRATEGY.md with primary sources and provisional model shortlist. Read development hardware: Ryzen 7 4800H, approximately 16 GB RAM, RTX 3050 Laptop GPU with approximately 4 GB VRAM. No model downloads or benchmarks performed. Photos/OCR are now explicit delivery requirements.

## 2026-09-26 — step 1 implementation

Built the new Tauri + React + TypeScript scaffold in apps/desktop. The working product name is Gather; branding remains provisional. Added a responsive sample library, combined type/text filters, no-results recovery, reader with explicit document scope, disconnected-chat state, and model lineup screen. GSAP entrance transitions respect reduced-motion preferences. All content is labelled synthetic; nothing claims to be semantic search yet.

Toolchain: installed the official Rust stable minimal MSVC toolchain (without modifying global PATH). Verified existing Visual Studio C++ tools. Added scripts/desktop.ps1 to select a compatible installed Node version and bypass the broken npm shim. Installed and locked JavaScript dependencies. Removed the template opener plugin and greeting command; the shell exposes no custom filesystem/shell capabilities. Added a content security policy.

Verification: three component tests passed (combined filters/empty-state recovery, selected-source navigation, and honest unconnected import/model states). TypeScript and production frontend build passed. Initial native Windows compilation passed. Dependency audit reported zero known vulnerabilities at installation time; this is not a security guarantee.

Visual review: the browser tool rejected opening the local preview because permission was declined. No alternate browser or screenshot workaround was attempted. Actual visual appearance, zoom, native interactions and motion remain unverified.

Next checkpoint: review this interface, then add the local processing boundary and a small reproducible embedding benchmark with synthetic text. The four recommended models are accepted starting candidates; no model weights have been downloaded and no Supabase project has been connected.

Final step-1 build: Tauri build --debug --no-bundle succeeded with bundled frontend assets. Executable: apps/desktop/src-tauri/target/debug/gather-desktop.exe. This is a development executable, not a signed installer. Runtime/visual verification remains pending. The temporary browser preview server was stopped.

## 2026-09-26 — design rules and attachment audit

Recorded every user-specified anti-template rule in DESIGN_AVOID_LIST.md, including the interpretation of the two garbled font/texture fragments. Added AGENTS.md so future work reads these rules. Reviewed all seven named design resources; adoption versus inspiration is explicit in the avoid-list resource table.

Implemented Motion-based selected-filter feedback, optional Lenis reader scrolling and a paused, labelled Thinking Orbs example. Removed Lucide and GSAP dependencies, reveal animation, slogan headings, serif heading styles and brightness/fade hover behavior. Added a local original contour SVG, spacing tokens and policy navigation. Main text/button token contrast ratios: 11.95:1, 6.35:1 and 9.30:1; this is not a full-screen accessibility audit.

Read and applied the supplied six-item audit prompt. Added PRIVACY_RELEASE_AUDIT.md with Found / Changed / You still need to for each item and a summary. Added accurate current-state policy screens; production policies and a working copyright report contact remain explicit release gates. No fictitious age gate, unsubscribe, billing or report endpoint was introduced where the underlying feature is absent.

Legacy code changes: removed Google Docs viewer URL requests containing local paths, changed fallback rendering to plain text and redacted dynamic console prints in main.py, main1.py and chroma.py. All three parsed successfully without running them. Data files and environment credentials were not read or changed.

Bundled production dependency license notices in public/THIRD_PARTY_NOTICES.txt. Every installed production package had a license file in the scan. Known-token-pattern source/bundle scan found no matches; this is not an exhaustive secret audit. Dependency installation reported no known vulnerabilities.

Component tests pass (four tests); canvas rendering is explicitly stubbed in jsdom tests and is not visually verified. Native appearance, keyboard navigation, zoom, optional scrolling and orb animation remain pending visual review. Previous browser access denial was respected; no browser workaround was used.

Final verification: all four component tests, TypeScript/frontend build and native Windows build with embedded assets passed after the final policy-footer changes. The existing gather-desktop.exe now contains this update. No cloud services or model downloads were activated.

## 2026-09-26 — TASK-001 structured workflow and version-control baseline

Adopted the user's Read -> Understand -> Plan -> Implement -> Test -> Review -> Fix -> Commit -> Update documentation loop. Added canonical PRD, architecture/design entry points, rules, tasks with acceptance criteria, decision log, current memory, test plan, security requirements and a blank future-public-config .env.example. Updated AGENTS.md and README to use these entry points. Generic Next.js/Vercel/Inter examples did not override the desktop stack or design avoid-list.

Found an existing repository on main with no commits and no remote, and reused it. Explicitly staged the current source, configuration, licenses and documentation as the first recovery checkpoint. Verified 74 baseline paths: no private-data directories, environment secrets, dependencies, model caches or compiled outputs were staged; no file exceeded 1 MB; known secret-token patterns returned no findings; Markdown links resolved. These are bounded checks, not an exhaustive security certification.

Four component tests and the production frontend build passed again. Relevant documentation diff whitespace issues were fixed. The full initial baseline diff reports existing whitespace issues in legacy/template files; no unrelated legacy formatting rewrite was performed. Lint remains unconfigured, native/visual QA remains unverified, and a public repository/remote is not configured. No product runtime changes in this checkpoint, so the prior native build evidence is retained rather than claiming a new native QA run.

TASK-001 is complete in the baseline commit containing this entry. Next: TASK-004 local processing contract using synthetic text only. Audience research, visual review and automated lint/CI remain explicit tasks. Nothing was pushed, published or uploaded.

## 2026-09-26 — GitHub repository created

At the user's request, created private repository https://github.com/kratos1911/gather-desktop using the existing authenticated GitHub account. Connected origin, pushed main, and verified remote commit b89ceec matches local HEAD. Reviewed all 74 tracked files before upload; excluded personal document folders, environment secrets, dependencies and build outputs. No model weights or original documents were uploaded. This is source hosting, not a production application release.

## 2026-09-27 — TASK-004 text-processing contract and cloud decision

User explicitly selected cloud AI, with hosting deferred. Recorded ADR-009,
superseded local inference in canonical architecture/product/rules/current state,
and labelled earlier blueprint/model research as historical where applicable.
Cloud provider, budget, queue and runtime remain undecided. No paid provisioning,
model downloads or external document processing occurred. Updated preview copy
to say cloud processing is planned and disconnected.

Implemented a dependency-free Python processing module in services/worker:
strict bounded JSON/base64/UTF-8 input, TXT/Markdown preservation, exact Unicode
code-point source ranges, deterministic content hashes/versioned passage IDs,
bounded overlap and fixed structured errors. Original source bytes are never
modified. No filesystem, network, logging, persistence or model calls in the
processor. Two committed fixtures and generated test inputs are synthetic.
The module is reusable in a future cloud worker, not an active server.

Verification:
- Bundled Python: `python -m unittest discover -s tests/worker -v`: 12 tests pass.
- `scripts/desktop.ps1 test` with compatible Node on PATH: four component tests pass.
- `scripts/desktop.ps1 build`: TypeScript/frontend build pass.
- Tauri CLI `build --debug --no-bundle`: final frontend/native development build
  passes; updated executable at apps/desktop/src-tauri/target/debug/gather-desktop.exe.
- Staged diff whitespace check passes. Explicit staged path review excludes
  private/generated content; limited known-token/private-key scan found no matches.

Review: clarified code-point versus JavaScript UTF-16 offsets, preserved BOM and
CRLF, rejected duplicate JSON keys/invalid request IDs/control bytes, verified
complete source reconstruction and deterministic retry identity. Removed stale
local-download wording found in the preview during review. Content identity is
not authorization; future persistence must scope deduplication by owner.

Limits: 64 KiB source is a conservative module limit, not the planned upload
limit. Character chunking still requires tokenizer validation in TASK-005.
Durable jobs, IPC/API integration, auth, semantic search, chat and cloud cost/
retention controls are unimplemented. Native runtime/visual/E2E QA remains
unverified; browser denial was respected. Lint is still unconfigured.

Checkpoint branch: feature/text-processing-contract. TASK-004 is complete to
its isolated processing criteria. Next is TASK-005 synthetic retrieval fixtures,
queries and expected evidence before cloud benchmark/provider deployment.

## 2026-09-27 — TASK-005 retrieval corpus preparation

Created text-v1, an original fictional English development set: 14 TXT/Markdown
documents, 40 queries and 37 labelled evidence spans across 35 answerable queries.
Categories: 20 paraphrase, 6 exact, 4 confusable, 3 late-document, 2 multiple-source
and 5 absent questions. Near-match receipts/schedules/bookings/stock figures
serve as distractors. A longer workshop handbook puts relevant evidence beyond
the first 1,024 characters. Absent questions have authored rationales.

Added scripts/prepare_text_evaluation.py using only standard-library code and
the existing processor. It validates unique IDs/questions, exact evidence,
chunk containment, late/multiple-source categories and absent labels; exports
index and queries separately from gold labels; pins a canonical corpus hash.
Default invocation prints inventory only. Generated exports stay in ignored
output/evaluation/text-v1, not in Git. No model/cloud/personal data was accessed.

Checks: seven evaluation unit tests pass; preparation/export produces 16 chunks
and fingerprint 07836c70107491a5a44d7d00c7f50bb69802c62b871841537e74163a8fdf6a4c.
TypeScript/frontend build passes. No UI/native inputs changed, so no native or
component rerun was needed. Reviewed source quotes and labels against documents;
staged diff whitespace and limited secret/path checks pass.

Documented document Recall@5, evidence Recall@5, MRR@5, category reporting,
missing-run rejection and separate absent-answer behavior. Scorer implementation,
lexical baseline and model benchmarks remain pending. The small authored corpus
is deliberately labelled development-only: no independent/held-out, multilingual,
visual/OCR, 10,000-chunk performance, isolation or chat quality claims.

TASK-005 stays partial. Next: offline scoring harness and lexical baseline,
followed by provider/model selection with budget before any paid evaluation.

## 2026-09-27 — TASK-005 scorer and keyword baseline

Implemented scripts/score_text_evaluation.py: label-free TF-IDF cosine ranking,
complete-run validation and per-query/category document Recall@5, MRR@5 and
evidence Recall@5. Runs pin both corpus and processed-index hashes; unknown,
duplicate, incomplete, mismatched or nonfinite results are rejected. Array order
defines rank. Document deduplication precedes the five-document cutoff; passage
scoring uses five chunks, with overlap counted once per expected evidence span.

Measured the unchanged text-v1 development corpus: document/evidence Recall@5
34/35 = 0.9714285714, MRR@5 0.8666666667. Only q18 misses expected evidence;
four of five absent questions return candidates. No answerability or semantic
claim is made. Reviewed this high score against the tiny 14-document/16-chunk
corpus and documented its limitations in tests/evaluation/BASELINE.md rather
than tuning data or claiming the product target achieved.

Checks: 21 evaluation tests pass, including 14 new scorer/baseline tests with
hand-calculated outcomes, stale/incomplete result rejection and cutoff cases.
Both direct baseline and saved-run CLI scoring pass. TypeScript/frontend build
passes. No desktop/native code changed; no native/component rerun claimed.
Reviewed staged paths and diff whitespace; limited secret scan found no matches.
Generated run/report JSON remains under ignored output/evaluation/text-v1.

No models, provider SDKs, network calls, personal data or paid resources involved.
TASK-005 remains partial until model/tokenizer/dimension/cost/latency benchmarks.
Next: provider/model benchmark configuration and adapter; budget/provider must
be selected before hosted evaluation. Cloud deployment remains deferred.

## 2026-09-27 — TASK-005 vector comparison foundation

Added scripts/evaluate_vectors.py: a saved-embedding adapter, consistent-space
validation, stable L2 normalization/exact cosine ranking, and equal-weight
reciprocal rank fusion with TF-IDF (k=60). Requires complete versioned exports
with model/revision/templates/tokenizer/dimensions, corpus/index hashes and no
truncation. Keeps zero/negative cosine candidates without claiming answerability.
CLI comparison retains provenance/configuration/rankings/reports together.

Explained techniques and controlled-comparison methodology during implementation
and in tests/evaluation/VECTORS.md. Cloud provider/producer is not implemented;
this checkpoint is a consumer for eventual exported embeddings. No model weights,
API calls, uploads, credentials or spending were involved.

## 2026-09-27 — Embedding request client; provider deferred

Added a server/developer-only client with token/request caps, all-input preflight,
bounded batches, response-index reordering, dimensions/model/vector checks,
optional usage accounting, HTTPS timeout/body bound/no redirects and sanitized
errors. Tests inject mock transport and tokenizer; none performs a network call.
Read Together's official embeddings API shape as candidate protocol only; model
availability and live provider behavior remain unverified. No default endpoint,
credentials, CLI or automatic retry. Token caps are not dollar spending limits.

User has no provider account and deferred it; no provider-specific benchmark,
truncation assurance or genuine vector export is claimed. User also required
explicit permission for every future push; recorded in AGENTS.md/RULES.md.
Twenty worker tests (eight new), 29 evaluation tests and frontend build pass.
No native assets changed. Continue independent TASK-011 quality tooling next.

Checks: 29 evaluation tests pass, including eight new hand-calculated vector
tests for cosine, magnitude stability, ties, invalid vectors, incomplete/mixed/
stale/truncated exports and rank-based fusion. TypeScript/frontend build passes.
No native or UI changes, so no native/component rerun. Reviewed staged paths and
diff whitespace; limited credential-pattern scan found no matches.

No real vector export/CLI quality benchmark has been run. Synthetic vectors are
test fixtures only; the prior TF-IDF measurements are unchanged. TASK-005 remains
partial. Next: provider/model/budget selection and a genuine embedding producer
with batching, token validation, bounded requests and usage accounting.

## 2026-09-28 — Local quality checks and bookmark scope

TASK-011: added frontend ESLint, explicit type/format checks, a fail-fast local
runner and a manual-only GitHub workflow. Fixed formatting reported on the first
run. Final local runner passes: 20 worker + 29 evaluation + four UI tests (53),
ESLint, TypeScript, Prettier and frontend build. Rebuilt native development
executable with `cargo build --locked --features tauri/custom-protocol`; passed.
No runtime/visual/E2E or remote CI verification claimed. Dependency installation
reported zero known vulnerabilities; this is not a complete security audit.

User added links/bookmarks, including social/video, blog and gaming URLs.
Recorded scope, flow, extraction limits, source provenance and restricted-fetch
requirements in BOOKMARKS.md and the product/architecture/design/security plans.
Technique: save first, enrich metadata/readable text separately, then reuse
chunking and retrieval. Preserve a URL/notes fallback when extraction is blocked.
TASK-016 is offline synthetic parsing; TASK-017 connects private persistence,
restricted network access and search. No bookmark functionality implemented yet.

Provider accounts, paid calls and cloud deployment remain deferred. Changes stay
local; no push or remote workflow dispatch authorized.

## 2026-09-28 — TASK-016 offline bookmark extraction; chat deferred

Implemented URL normalization/validation, metadata and main/article text extraction,
body fallback, paragraph offsets, content hash/version and explicit unavailable
reasons. Bounded UTF-8 input and HTML nesting; preserves notes when extraction
is unavailable. No network requests, model calls, personal inputs or dependencies.
This does not save bookmarks in the desktop or produce semantic search results.

Ten new synthetic tests cover URL rejection, metadata-only video links, malformed
HTML, Unicode/entities, malicious elements, limits, deterministic extraction and
fallback. Full local quality runner passes: 30 worker + 29 evaluation + four UI
tests (63), lint, types, formatting and frontend build. No native inputs/assets
changed; no native rebuild or visual/runtime verification claimed this turn.

Chat deferred per user. Next TASK-018 connects bookmark evidence to versioned
passages and keyword retrieval, independently of provider setup. Live fetching
still requires network security and privacy gates. Keep all commits local.

## 2026-09-30 — Obsidian project knowledge base

Found an existing .obsidian vault in the repository with a root daily note and
Untitled.canvas. Preserved both. Added PROJECT_HUB, concept glossary, accepted
ideas/open questions, maintenance workflow, session/idea templates and a search
flow canvas with implemented/planned/deferred states. Added AGENTS maintenance
instructions so future work consults and updates these notes. Configured local
template and daily-note paths; ignored .obsidian settings/workspace in Git.

Checked new internal links, canvas IDs/edges/file references and configuration
JSON on disk. No Obsidian window interaction or visual verification performed.
Documentation-only change; no app tests/build rerun. Latest code evidence remains
63 tests and frontend quality/build checks from 28 September. Corrected stale
worker-test counts in state/task summaries. TASK-018 remains next. No push.

## 2026-09-30 — Agent Reach integration direction

Reviewed the upstream English README and package metadata. Recorded the user's
extraction-toolkit preference, public-page adapter scope, third-party reader
boundary, desktop-session Instagram limitation and separate save/index states.
Updated Obsidian hub, bookmark/architecture notes, current state and TASK-019.
No package installed, browser session accessed, URL scraped or model invoked.
Documentation-only checkpoint: diff and local note references checked; application
checks not rerun. TASK-018 remains next and chat remains deferred. No push.

## 2026-09-30 — Extraction stack accepted

Recorded user acceptance of Crawl4AI plus yt-dlp. Updated current architecture,
bookmark plan, TASK-019, state and Obsidian hub; retained Agent Reach research
with an explicit superseded banner. Added EXTRACTION_STACK with scope, source
links, adapter boundaries and acceptance gates. No dependencies installed or
network extraction performed. TASK-018 remains the next implementation task.
Documentation-only checks: internal links and diff whitespace; no app build or
tests rerun. Prior 63-test result remains historical evidence. No push.

## 2026-09-30 — Repository cleanup

Inventoried all 109 tracked files, read tracked bytes, parsed Python syntax without
execution and checked active entry points/references. Archived six original root
prototype files unchanged in legacy/ with explicit unsupported/reference status.
Deleted three unreferenced scaffold SVG logos and root .DS_Store metadata. Kept
native icons, lockfiles, licences, source, tests and documentation. Preserved
private data/secrets, environments, generated outputs and user canvas. No legacy
code was run; this was not a full correctness/security review of every module.

Checks: 30 worker + 29 evaluation + four UI tests pass; lint, types, formatting
and frontend build pass. Native development executable rebuilt successfully via
cargo build --locked --features tauri/custom-protocol. Visual/runtime verification
remains pending. Updated onboarding, architecture and Obsidian hub/state; full
per-file record in REPOSITORY_AUDIT.md. TASK-018 remains next. No push.

## 2026-09-30 — TASK-018 bookmark passage adapter

Implemented bounded HTML extraction to field-specific versioned passages, reusing
text-processing request validation/chunking. Preserved original URL, exact field
offsets, extraction status/reason and semantic_ready=false. Revision/source/field
identities distinguish retries, edited notes and separate sources. Notes and URL
remain processable when extraction is unavailable; invalid field processing
returns no partial document. Documented contract in services/worker/BOOKMARK_PASSAGES.md.

Seven new tests pass, including late-document TF-IDF retrieval resolving back to
source URL and matching excerpt. Full runner: 37 worker + 29 evaluation + four UI
= 70 tests; lint, types, format and frontend build pass. No native inputs changed,
so native build not rerun. No live scraping, storage, model or UI integration.
Updated Obsidian hub and canvas. TASK-019 is next. No push.

## 2026-09-30 — TASK-019 output normalization checkpoint

Added pure Crawl4AI Markdown/metadata and yt-dlp single-video metadata/normalized
subtitle-cue adapters. Preserves backend version, retrieval timestamp and final
URL where supplied; handles HTTP/extraction failures without copying raw errors.
Cue timing/language/automatic flags survive passage chunking. Added generic text
bounds and input checks; no tools, subprocesses, models or network fetching.

Eight new synthetic tests pass. Full checks: 45 worker + 29 evaluation + four UI
= 78 tests; lint, types, formatting and frontend build pass. No native inputs
changed; native build not rerun. Official protocol docs reviewed; actual package
compatibility is unverified. TASK-019 partial: isolated runner, pins/licenses,
VTT/SRT parsing and network/privacy checks still pending. Obsidian notes updated.
No push.

## 2026-09-30 — Subtitle parsing checkpoint

Added bounded SRT/WebVTT caption parser: UTF-8/BOM/line-ending handling, timestamp
validation, cue identifiers, display-markup removal, entity decoding, overlap
preservation and size/count limits. Unsupported formats and malformed blocks
raise generic errors without returning a partial transcript. This is a subset,
not full WebVTT rendering/conformance. No external dependencies or live downloads.

Eight new tests, including subtitle bytes through yt-dlp output adapter to passage
cue references. Full runner passes: 53 worker + 29 evaluation + four UI = 86 tests;
lint, types, formatting and frontend build. Native inputs unchanged; no rebuild
or visual QA claimed. TASK-019 still partial; next isolated/pinned extraction
runners and network controls. Updated Obsidian state/hub. No push.

## 2026-09-30 — Extractor destination policy and direct pins

Implemented pure public-destination preflight with injected DNS, all-answer
validation, port restrictions, sanitized resolver errors and immutable approved
addresses. Eight tests cover mixed/private/metadata/special ranges, malformed or
large answers, literal IPs, numeric hosts and changed DNS answers. This does not
perform network I/O or prevent rebinding unless the future transport uses the
approved addresses. No isolation or live runner claim.

Recorded PyPI-verified direct pins in requirements-extraction.txt. Not installed;
transitive lock and complete dependency licence review remain pending. Full
checks pass: 61 worker + 29 evaluation + four UI = 94 tests; lint, types, formatting
and frontend build. Native assets unchanged; no native rebuild. TASK-019 partial.
Next: enforced network execution boundary and isolated extractor environment.
No cloud provisioning, personal browser access or push.

## 2026-09-30 — Offline runner and container configuration

Added bounded one-job stdin/stdout runner with strict fields, duplicate-key
rejection, generic errors and no shell dispatch. Added Dockerfile, allowlisted
build context and Compose configuration with no network, no host mounts,
non-root/read-only filesystem, dropped capabilities and resource limits.
Compose configuration validates. Docker Linux engine unavailable; attempted
hidden Docker Desktop start but engine remained unreachable. Image build and
installed packages/isolation unverified; no live scraping performed.

Four runner tests added. Full local runner passes 65 worker + 29 evaluation + four
UI = 98 tests, lint/types/format/frontend build. No native inputs changed. TASK-019
remains partial: restore Docker engine, build/lock image, enforce egress and add
live tool execution. No push, browser-session access or paid provisioning.

## 2026-10-01 — Built and checked offline extraction container

Docker Linux engine became available. Built the image successfully; verified
Crawl4AI 0.9.4 and yt-dlp 2026.8.19 package metadata and pip dependency consistency.
Added repeatable scripts/check_extractor_container.py: synthetic success/error
jobs, semantic_ready false, UID 65532, rejected application-directory write,
unreachable external route, and absence of /app/.env and /app/data all pass.
Smoke containers removed on exit. These probes do not certify production isolation.

Reran 65 worker + 29 evaluation + 4 UI = 98 tests, lint, types, formatting and
frontend build successfully. No native inputs changed; no native rebuild needed.
Updated canonical status, hub, extraction note and Obsidian flow canvas. TASK-019
remains partial: dependency/base-image locks, public-only egress, browser runtime
and actual tool invocation/live compatibility remain open. No live scraping,
cloud provisioning, personal-document processing or push performed.

## 2026-10-02 — Search-first system and delivery plan

Reviewed desktop fixture path, native capabilities/CSP, offline runner, network
preflight, Compose and product/security notes. Product Design preflight found no
saved context; existing project conventions were used. DELIVERY_PLAN.md records
target flows, a minimal backend, private data model, leases, version publication,
deletion races, hybrid retrieval, security controls and ordered acceptance gates.
ADRs 026–028 are proposals; TASK-019A/B/C and TASK-021 describe implementation work.
Consulted official Supabase, pgvector, OWASP, Tauri and Cloud Run references.
No runtime changes, cloud deployment, paid call or push. The prior 98-test result
is historical evidence, not a new test run. Documentation diff checks pass;
architecture artifact evidence is recorded separately after generation.

Architecture artifact: .archify/architecture-gather-plan-20261002-081351/.
Archify deliver and strict provenance check passed all nine structural checks,
with zero errors/warnings/crossings and 13 verified source references at c0b628f.
Browser/perceptual checks not run because the prior browser restriction remains;
standalone delivery used instead of finalize's browser gate. The artifact README
records this limitation and the aspirational text-size target miss. Hub and
Obsidian flow canvas link the plan. No application source changed or runtime
tests rerun. Planning and artifact checkpoints committed locally; nothing pushed.

Artifact review follow-up: Git flagged 15 whitespace-only lines in the generated
viewer. Preserved generated bytes and recorded the exception rather than alter
the hash-bound output. Added exact-byte Git attributes for candidate/HTML/receipt
to keep provenance stable on Windows checkouts. Authored-document checks pass.

## 2026-10-02 — Extractor lock and advisory review; storage blocker

Recorded user's OKF acceptance as an optional later linked-note/export feature,
not a replacement for Supabase/hybrid retrieval or the later RAG chat path.
Added ADR-029, learning notes and the deferred idea; no OKF runtime installed.

TASK-019A: resolved the existing tested image's 96 application packages into exact
Linux/amd64 CPython 3.12 wheel hashes and declared license inventory. Pinned the
base platform manifest, added hash-enforced wheel-only installation and separate
pip 26.2.1 bootstrap lock after advisory review of base pip 25.0.1. Added repeatable
lock/advisory scripts, exact installed-package smoke comparison and eight tests
for drift/omissions/bad artifacts, inventory consistency and fail-closed feed errors.

Full local checks pass: 73 worker + 29 evaluation + four UI = 106 tests, lint,
types, formatting and frontend build. No native inputs changed. PyPI lookup of
96 packages plus target pip succeeded with zero lookup errors and one affected
package: NLTK 3.10.3, GHSA-8mgp-746c-j5xp. No patched release listed; recorded a
live-extraction gate. The advisory script correctly exits nonzero for this finding.

Docker no-cache rebuild failed after C: reached zero free space and Docker reported
read-only filesystem / image-store I/O errors. Stopped the build client. Scout's
first temporary export ran out of C: space; a project-drive retry failed on Docker
storage. No successful new-image build, smoke, intentional hash-mismatch rejection
or OS scan claimed. No user files/caches/images were deleted or storage reset.
TASK-019A stays partial. Restore storage and restart Docker, then rebuild/test/scan.
Details: services/worker/DEPENDENCY_REVIEW.md. Notes/hub/canvas updated; no push.

## 2026-10-03 - Docker recovery and locked-image verification

Resumed after Docker restart. No-cache image build completed successfully with
hash-enforced wheel installation and pip check. Exact locked package comparison,
synthetic success/error jobs, non-root UID, read-only application path, unreachable
external network and excluded personal paths pass. An actual pip probe rejects a
wrong artifact hash and accepts its correct hash.

Added unique smoke-container names and explicit removal in finally, including
client timeout. Three mocked cleanup tests pass; a real deliberately sleeping
container times out and is removed. No gather-smoke containers remain. This is
developer verification tooling only, not TASK-019B production job supervision.

Docker Scout full scan completed: 51 records, 10 high / 7 medium / 34 low / no
critical. Aliases may overlap. IMAGE_SCAN_REVIEW.md records the image/report hash,
complete inventory and remediation categories. OS patches, pip bundled libraries
and NLTK remain open. Static inspection found Crawl4AI NLTK tokenizer/downloader
paths; no live extraction was executed. TASK-023 now tracks remediation before
networked execution. TASK-019A build/audit acceptance is verified, not security
readiness or completion of TASK-019.

Full quality runner passed: 76 worker + 29 evaluation + four UI = 109 tests,
ESLint, TypeScript, Prettier and frontend build. No native inputs/assets changed;
no native rebuild or visual/E2E claim. State, task board, decision, dependency,
runner, test, delivery and Obsidian hub/concept/canvas notes updated. No paid
resources, personal documents or GitHub push. Changes committed locally.

## 2026-10-03 - TASK-023 available fixes and full rescan

Pinned installed OpenSSL/libssl/provider to 3.5.7-1~deb13u3 and PCRE2 to
10.46-1~deb13u3 using authenticated Debian security metadata. Removed pip and
ensurepip from runtime; developer installer target retains checksum/dependency
checks. Build succeeded, reusing unchanged hashed-wheel install layers. Runtime
smoke verifies all 96 application versions, patched OS versions, absent installer
modules, isolation, synthetic jobs and installer hash rejection/acceptance.

Rescan completed: 31 records (4 high, 2 medium, 25 low), versus 51 (10/7/34).
Twenty-one prior records disappeared; CVE-2026-95619 is newly reported by the
refreshed feed. Complete report hashes, inventories, references and dispositions
are in IMAGE_SCAN_REVIEW.md. Remaining NLTK/GCC/zlib and lower-severity records
stay open; TASK-023 is partial. No clean-security/live-extraction claim. Scout
reported a locked temporary archive during cleanup, but wrote a valid SARIF.

Real smoke exposed delayed Windows cleanup: subprocess.run can wait for child
pipes after killing Compose. Changed to explicit process lifecycle, kill/remove
before closing pipes. Three regression tests cover ordering, auto-removal and
cleanup errors. Real 120-second sleep now cancels within a 20-second budget;
whole final smoke completed in under ten seconds. No smoke containers remain.

Full checks passed: 109 tests, lint, types, format, frontend build. After cleanup
change, all 76 worker tests and real smoke were rerun successfully. No native
inputs/assets changed. Docs and Obsidian notes/canvas updated. Local commit only;
no cloud spending, browser use, real documents or GitHub push.

## 2026-10-03 - TASK-019B controlled transport and offline supervisor

Added backend-only restricted_fetch: public-address approval, numeric-IP dialing
without second DNS, peer/TLS identity checks, per-redirect validation, downgrade
rejection, bounded identity-encoded page bodies and safe errors. It does not
follow scripts/assets, forward cookies/headers, or use proxy environment settings.
Known NAT64 translation ranges are now denied. Fifteen tests use controlled local
HTTP peers plus injected resolver/TLS checks; no public sites or DNS were queried
by the test suite. Initial stall test exposed a missing explicit read timeout on
an injected socket; fixed it and reran all worker checks. Slow-header rejection
and elapsed-time bounds also pass. Whole-broker DNS deadline remains open.

Added host-side DockerJobRunner with operator image digest, fixed command,
network none, non-root/read-only/capability limits, one local concurrency slot,
input/stdout/stderr caps, timeout/cancellation and exact-container cleanup.
Five prelaunch unit tests and real Docker adversarial probes pass: supplied-output
success/error, timeout, cancellation, excessive stdout/stderr, invalid output,
failed process, recovery, direct public/private/metadata egress denial, absent
socket/secrets, read-only path, UID and cgroup resource limits. No job containers
remain. Docker supervision is not a durable queue or a hosted API; supervisor
crash/orphan reconciliation and distributed quotas remain planned.

Validation: scripts/check.ps1 passed the 96-worker/29-evaluation/four-UI suite,
lint, TypeScript, Prettier and frontend build. Added the slow-header case and reran
all 97 worker tests successfully: current total 130 tests. Final image rebuilt;
check_worker_supervisor.py passed against it. Scout rescan completed with the same
31 advisory IDs (4 high, 2 medium, 25 low), documented with image/report hashes.
Scout temporary archive cleanup reported a file lock; valid SARIF was retained.
No dependency findings were suppressed. No native inputs changed or native E2E
claim made. Browser access, live extraction, paid AI and public deployment remain
off. TASK-019B remains partial: next is a supervised fetch-broker process covering
DNS, then parser integration and browser/tool egress. Canonical docs, concepts,
Obsidian hub and flow canvas updated; local commit only, no GitHub push.

## 2026-10-08 - Whole-fetch deadline and controlled page-to-passages flow

Implemented FetchBroker with one fixed child process per URL, parent deadline
covering DNS/connect/TLS/body operations, cancellation, bounded input/output and
safe errors. Child startup is isolated; only Windows system-directory variables
are inherited, with no provider/proxy/Python environment settings. Timed-out and
cancelled processes are killed/reaped and pipes closed; valid output from a child
that remains running is not published. This is lifecycle isolation, not a host
filesystem/memory/network sandbox or general process-tree supervisor.

Added http-page adapter and BookmarkPipeline. Actual fetched HTML/XHTML or UTF-8
plain bytes pass to the network-none Docker parser; source notes, original/final
URL, timestamp, redirects, body hash and passage provenance are preserved. This
is explicitly restricted-http output, not simulated Crawl4AI or semantic results.
Fetch failure/cancellation never invokes the parser; durable bookmark preservation
still belongs to the future storage/coordinator layer.

Nine broker and six page/pipeline tests added. Tests simulate blocked DNS, connect
and TLS within real subprocesses, check output flooding/schema failures, recovery,
reaping, secret environment exclusion and cancellation between stages. A first
oversize-result fixture exceeded Windows command-line length; changed only that
fixture to construct its large output inside the child, then verified rejection.
Full quality runner passed with 110 worker + 29 evaluation + four UI tests and
lint/types/format/frontend build. Added two more edge cases and reran all 112
worker tests successfully: current total 145. No native inputs changed.

Docker image rebuilt successfully with unchanged package layers.
check_bookmark_pipeline.py passed: loopback HTTP redirect -> real broker child ->
real offline Docker parser -> passages, plus metadata-redirect rejection before
parsing. No real websites, browser tools, personal documents or paid services used.
No job containers remain. Scout rescan: 29 records (2 high, 1 medium, 26 low),
versus 31 on 3 October. No package fixes were made this turn: two GCC records are
no longer reported by the feed and one advisory severity changed. Full current
inventory, image digest and SARIF checksum recorded in IMAGE_SCAN_REVIEW.md.
The scanner again reported a locked temporary archive during cleanup but wrote
valid SARIF. Remaining dependency and production gates stay open.

Canonical docs, Obsidian hub/concepts and flow canvas updated. TASK-019B remains
partial for browser/tool egress, production broker confinement and public/TLS
compatibility. Local persistence TASK-021 can proceed independently. No push.
# 8 October 2026: TASK-021 source ownership foundation

Added Supabase-targeted sources/source_versions migration and disposable pinned
PostgreSQL 17 checks. Nineteen SQL assertions pass: two-user isolation, own
metadata persistence, owner/lifecycle write denial, anonymous/missing identity,
composite owner foreign key and tombstone/dependent-version visibility. The
container uses no network/ports/host mounts, bounded tmpfs, and was removed after
the run. Unrelated Docker services were not changed.

Existing quality runner also passes: 112 worker + 29 evaluation + 4 UI tests,
lint, type checks, formatting and frontend build. No native inputs changed.
Reviewed SQL privileges and ownership boundaries; no client insert/delete grants
until quota/cleanup APIs exist. Updated canonical notes, Obsidian hub/concepts
and flow canvas. Changes committed locally only; no push.

Limits: this uses a test-only Auth contract shim on PostgreSQL, not full Supabase
services or JWT validation. Storage/RPC, durable jobs, quota/retry/delete races,
worker persistence and desktop integration remain pending. TASK-021 stays partial.
Live extraction security gates and cloud AI account deferral remain unchanged.

## 9 October 2026: atomic saves and database cleanup

TASK-021 now includes source-count quotas, idempotent save receipts, atomic
tombstone/cleanup requests, database-only cleanup and late-version write guards.
45 SQL assertions plus four concurrent scenarios pass on disposable PostgreSQL.
These cover repeated/conflicting saves, rollback, quota exhaustion, ownership,
late retry after deletion, duplicate cleanup and derivative write/delete races.
No default production quota, account creation, Storage or desktop connection.

Docker was initially unavailable; the later run with Docker access succeeded.
The initial sandboxed quality run could not complete local-network tests and was
stopped. The authorized run outside the sandbox passed all 145 existing tests,
lint, typecheck, formatting and frontend build. No native inputs changed.
Updated architecture, decision, state, task, test and Obsidian hub/concepts/map.
Local checkpoint only; no push. TASK-021 stays partial for Supabase integration,
external cleanup, byte/rate budgets, receipt retention and processing leases.

## 9 October 2026: real core Supabase API and original-file deletion checks

Added a private originals migration and Storage-presence guard before SQL cleanup.
A new disposable Compose harness runs actual Auth/PostgREST/Storage with synthetic
users and TXT bytes. All 31 API checks pass, including JWT login, ownership, denied
client mutations, immediate tombstone visibility, failed-cleanup preservation,
Storage API byte removal, interruption before finalization and retry safety.
The 49 database checks and existing 145 tests also pass, plus lint, types,
formatting and frontend build. No native inputs changed.

The initial CLI experiment exposed ports beyond loopback despite its documented
network option. It was stopped before proceeding; the final harness explicitly
publishes only 127.0.0.1:55431 and checks Docker bindings. The first Auth setup
disabled email/password login with email signup; the final setup keeps the
provider enabled and public signup disabled. Test schema permission/startup
issues were fixed and verified against the actual APIs.

CLI initialization enabled its usage-reporting setting; it was disabled during
setup. No product telemetry was added. Its stopped test volumes/networks were
removed, as were the successful harness's users/files/containers. Downloaded
tooling remains ignored and image caches remain; unrelated workloads were not
changed or pruned. No cloud resources or paid calls; local checkpoint only.

Updated tasks/state/architecture/security/test notes and Obsidian hub/concepts/map.
TASK-021 remains partial: this verifies core services, not hosted parity or desktop
persistence. Upload fencing, background cleanup/reconciliation, session lifecycle,
production dependency review and processing job leases are still open.

## 2026-10-10: real Qwen CPU benchmark on D:

User authorized model testing with downloads on D: due to low C: storage, then
chose Qwen first while EmbeddingGemma license acceptance is pending. Read canonical
docs and retained the search-first scope; chat and visual/OCR tests remain deferred.
Recorded later Cloud Run CPU/R2/Supabase choices without deploying paid resources.

Added a dedicated D: environment/cache/temp runner, fixed Qwen commit and artifact
hash verification, safetensors-only offline loading with remote code disabled,
exact-token preflight and real vector exports into the existing cosine/RRF scorer.
CPU dependency versions are frozen in a separate developer constraints file.
Unit tests cover token overflow/special tokens, invalid vectors, normalization and
rejection of C: storage. The new environment is isolated from the worker image.

Download: ten artifacts, 1,207,487,158 bytes; revision
97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3. All model/dependency artifacts remain in
ignored output/model-benchmark on D:. Download/package network restrictions required
approved reruns. Available RAM initially measured about 2 GiB; asked the user to
free memory. They agreed, and both actual runs passed the 4 GiB pre-load guard.

Both two/four-thread CPU float32 runs completed on all 16 passages and 40 queries.
Actual maximum input was 159 passage tokens and 35 prompted-query tokens; no input
was truncated. Dense 256/512/1,024 dimensions each scored 100% document/evidence
Recall@5 on 35 answerable queries; 512-dimensional MRR was 0.9857. Fixed RRF reduced
MRR; 1,024-dimensional hybrid also lost q18 evidence. All five absent questions
still return neighbors. These are genuine model outputs on a small fictional
development set, not production accuracy or an answerability evaluation.

Warm median/p95: 0.707/0.888 seconds at two threads; 0.324/0.376 at four. OS peak
working set about 3.64 GiB. Model loading follows hash reads, so its time is not
cold-start evidence. Laptop results do not predict Cloud Run prices or capacity.
Full raw vectors/reports stay ignored; concise machine-readable evidence with
raw-artifact hashes is in tests/evaluation/results/qwen-cpu-20261010.json.

The full check runner passed 112 worker, 33 evaluation and 4 UI tests, lint, types,
formatting and frontend build. Existing loopback tests initially failed/stalled
inside the network sandbox; the approved full rerun passed. A final storage-guard
test was then added and the evaluation suite rerun (34 tests). Pip check passes.
Native assets/inputs were unchanged. No personal files, hosted inference, app
integration, paid deployment or GitHub push. TASK-005 remains partial; next is a
broader evaluation and bounded serving-container measurement before selecting
dimensions/fusion and deployment sizing. Updated canonical and Obsidian notes/map.
