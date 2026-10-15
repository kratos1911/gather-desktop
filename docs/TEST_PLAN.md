# Verification plan

## Current executable checks

`python -m unittest discover -s tests/inference -v` runs 25 synthetic process/protocol/reporting/chunking
boundary tests: reuse/readiness, input and aggregate token limits, normalization,
busy rejection, startup/request deadlines, crash redaction, cleanup and explicit
restart. Included in scripts/check.ps1. These do not verify real model quality.
`python -m scripts.check_inference_runtime` separately verifies a pinned D: model
and measures host startup/three fictional requests; passed on 13 October after
RAM became available. The same 18 tests now also pass in the isolated Linux
image via `python -m scripts.check_inference_container --controls`. Container
configuration assertions pass; real Qwen container smoke passed on 14 October
with ten short fictional requests, model/vector checks and no OOM. Evidence:
tests/inference/results/qwen-container-20261014.json.
Extended profiles and image review are recorded in services/inference/PROFILE_RESULTS.md
and IMAGE_SCAN_REVIEW.md. Long inputs exposed deadline failures; scan findings
remain open. On 15 October the patched image passed six-case vector/token/rank
compatibility and five real 306–500-token chunks under the 15 s deadline. Evidence:
tests/inference/results/patched-{compatibility,comparison,chunks}-20261015.json.
Paired retrieval subsequently passed the text-v2 gate, but boundary context and
multi-part passage coverage remain open; see CHUNK_RETRIEVAL_RESULTS.md. HTTP
ingress and remaining security/licence review are still gates. These fixtures
are not full real-user quality regression.

`python scripts/check_database.py` separately runs 45 SQL assertions and four
concurrent scenarios against a
disposable pinned PostgreSQL image. It checks two-user reads/metadata edits,
column restrictions, owner foreign keys, anonymous/missing identity denial and
tombstone visibility, atomic quota/idempotency, cleanup rollback, repeated cleanup
and concurrent save/write/delete behavior. Test-only auth shim: full
JWT/Auth/Storage/PostgREST behavior is tested separately. See ../supabase/README.md.

`python scripts/supabase_test_stack.py` passes 31 checks using real local Auth,
PostgREST and Storage services: actual JWT sign-in, RPC ownership, private original
reads, denied uploads/overwrite/delete, tombstone visibility, failed cleanup guard,
API deletion and interrupted/repeated finalization. It uses synthetic users/files,
bounded temporary data mounts and an explicit loopback-only gateway. Services and
data are removed afterward. Exact hosted parity, concurrent upload fencing,
background reconciliation and desktop sessions remain unverified.

`python -m unittest discover -s tests/worker -v` (Python 3.11+) includes 12 synthetic
text-processing tests: exact source coverage, Unicode/BOM/CRLF, boundary/overlap,
stable retry IDs, empty/invalid/oversized/binary inputs, response bounds and
recovery without content in errors. No cloud, model or private-data access.

From repository root: `./scripts/check.ps1` runs 112 worker tests (nine fetch-broker subprocess, six HTTP-page/pipeline, 15 restricted-HTTP transport, five supervisor, three smoke-container cleanup, eight lock/audit, four runner, nine network-policy, eight subtitle, eight extraction-adapter, seven bookmark-passage, ten bookmark, 12 processing
plus eight mocked embedding-client tests), 29 evaluation tests, frontend ESLint,
TypeScript, Prettier, four component tests and frontend build. Use `-Python` to
specify a Python executable. These local checks pass; the manual GitHub workflow
is authored but has not run remotely. Use the documented Tauri build for native
changes; the latest native development build passes. Runtime/E2E remains unverified.

The four tests cover combined filters and empty recovery; selected-source navigation; honest disconnected import/model state; accurate privacy/copyright navigation. jsdom cannot prove browser/native rendering, GPU performance, accessibility or inference.

## Planned feature checks

| Area | Required cases |
| --- | --- |
| Worker/extraction | Empty/malformed/oversized/unsupported input, stable locations, all document sections, safe errors |
| Ingestion | Restart, retry, duplicate content, partial failure, missing source, quota, bounded concurrency |
| Bookmarks (planned) | URL validation, metadata/article provenance, inaccessible-page fallback, malicious HTML, size limits, private-address/redirect/DNS-rebinding rejection, duplicate/refresh/restart/delete and two-user isolation; see BOOKMARKS.md |
| Auth/access | Signup policy, login/logout/expiry, wrong credentials, two-user denial on every file/chunk/chat/storage/search path |
| Retrieval | Paraphrases, exact identifiers, late-document passages, no-answer queries, owner filtering, model-version mismatch |
| Photos/OCR | Visual descriptions, rotation/small text, confidence, separate-space fusion, source locations |
| Chat | Selected-source isolation, follow-ups, grounded citations, absent evidence, prompt injection, cancellation and timeout |
| Deletion | Immediate exclusion, all derivatives removed, Storage failure retry, restart during cleanup |
| UI | Loading/empty/error/offline states, keyboard/focus, screen reader labels, reduced motion, narrow windows and 200% scaling |
| Installer | Clean Windows machine, cloud setup, update, uninstall/data choice, no Python/dev tools or model downloads required |

## Evaluation and E2E

Text development fixtures and the scoring specification live in
`tests/evaluation/README.md`. Run `python -m unittest discover -s tests/evaluation -v`
for 29 corpus/scoring/baseline/vector tests and `python -m scripts.prepare_text_evaluation`
for a version/fingerprint/category summary. Optional `--output output/evaluation/text-v1`
exports index, questions and separate labels using the real text processor.
Current inventory: 14 documents, 35 answerable + 5 absent questions, 16 chunks.
`python -m scripts.score_text_evaluation` runs the offline keyword baseline and
exports rankings and metrics. `--run path/to/run.json --output output/evaluation/rescored`
scores existing rankings. Tests verify hand-calculated partial recall/MRR,
document deduplication before cutoff, sixth-document exclusion, passage evidence,
overlap, absent denominators, malformed/missing/stale rankings and deterministic
keyword retrieval. No AI model accuracy or latency has been measured. Baseline
results are in tests/evaluation/BASELINE.md; unsupported-answer rate stays null
until an answerability system exists.

Vector tests use known numbers to verify normalization/cosine, negative scores,
extreme finite magnitudes, ties, incomplete/mixed/stale/truncated exports and
RRF rank fusion independent of raw score magnitude. They are not semantic
quality tests. See tests/evaluation/VECTORS.md for the export contract and CLI.
Real Qwen exports have now been exercised by the separate CPU benchmark;
hosted inference is still unverified.

Version synthetic/approved fixtures, queries, model/runtime versions, hardware and results. Start with >=30 text and >=20 visual/OCR queries as described in MODEL_STRATEGY.md. Measure quality by category, not only aggregate accuracy. Proposed thresholds are not current results.

Native end-to-end flow: install -> cloud setup/sign in -> import -> wait for ready -> search with different wording -> open cited source -> ask question -> restart -> retrieve again -> delete -> verify absent -> sign out. Repeat with user isolation, slow network, quotas and failure recovery. Cloud-provider spending/retention controls require verification before hosted tests.

Choose the native/browser test harness in TASK-011/013. Browser tests alone do not cover Tauri capabilities or local workers. Do not introduce another browser tool to bypass the prior access denial.

## Completion evidence

TASK-005 local CPU export: run tests/evaluation/test_cpu_benchmark.py for token
limits (including special tokens), invalid vectors and reduced-dimension
normalization. Unit tests require no third-party ML dependencies or downloads.
Use scripts/benchmark-cpu.ps1 separately for real model evidence on the fictional
corpus. Verify D: cache paths, immutable model hash, no truncated inputs, complete
vector exports, per-category failures and memory/latency reports. Compare all
dimensions using the same frozen queries. Resource guards must fail before load.
See CPU_BENCHMARK.md. Do not relabel laptop timing as measured cloud cost.

Text-v2: use the fixed --corpus text-v2 option throughout preparation, model
export and scoring. Validate the corpus freeze before inference, keep labels
separate and preserve v1 outputs. test_challenge_corpus.py checks mutations,
source/query disjointness, late evidence, directory separation and mixed-corpus
rejection. Follow tests/evaluation/TEXT_V2_PROTOCOL.md without retrospective tuning.
Review every nonperfect primary-candidate query; see TEXT_V2_RESULTS.md.

Chunk-policy comparison: scripts/evaluate_chunk_retrieval.py freezes both layouts,
the fictional boundary corpus, protocol hash and deduplicated request order before
the patched container runs. Legacy and token512 use the same model/runtime and
512-dimensional vectors. Score unchanged exact quotes; uncontained spans remain
strict misses. Supplementary union coverage must reject gaps and mixed sources.
Tests cover legacy-index equivalence, label preservation, frozen edits and coverage.
Keep the 15 s per-request limit; the 900 s outer limit only allows more sequential
fixtures. Runtime/plan/image/raw-output hashes must match before scoring.

Record exact commands, passed/failed/not-run results and limitations per task. Review code after tests. Fix material issues before a completion commit. Documentation-only changes require link/state/diff checks, not unnecessary full installer builds.


## Extractor runtime remediation checks

Build both installer target and runtime per services/worker/RUNNER.md, then run
scripts/check_extractor_container.py. Verify exact patched Debian versions, all
96 application versions, absent pip/ensurepip and existing isolation checks.
Installer-only synthetic checksum probe must reject a wrong hash and accept the
correct one. A deliberate 120-second sleep must be cancelled and cleaned up
within 20 seconds, including Windows inherited-pipe handling. A full image rescan
is required after dependency/image edits; open findings remain release gates.


TASK-019B: run `python scripts/check_worker_supervisor.py` against the rebuilt
runtime. It verifies synthetic success/errors, timeout, cancellation, both output
limits, recovery, kernel resource settings, blocked direct egress and no leftover
containers. HTTP unit tests use controlled loopback peers and injected public DNS
answers, never real websites. TLS identity checks are mocked, not full certificate
handshakes. Broker-wide DNS/connect/TLS cancellation now passes subprocess tests. Browser
egress remains unverified. Run scripts/check_bookmark_pipeline.py after rebuilding
the worker to verify controlled HTTP -> fetch child -> offline Docker -> passages.
