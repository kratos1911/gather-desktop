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

Checks: 29 evaluation tests pass, including eight new hand-calculated vector
tests for cosine, magnitude stability, ties, invalid vectors, incomplete/mixed/
stale/truncated exports and rank-based fusion. TypeScript/frontend build passes.
No native or UI changes, so no native/component rerun. Reviewed staged paths and
diff whitespace; limited credential-pattern scan found no matches.

No real vector export/CLI quality benchmark has been run. Synthetic vectors are
test fixtures only; the prior TF-IDF measurements are unchanged. TASK-005 remains
partial. Next: provider/model/budget selection and a genuine embedding producer
with batching, token validation, bounded requests and usage accounting.
