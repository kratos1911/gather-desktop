# Verification plan

## Current executable checks

`python -m unittest discover -s tests/worker -v` (Python 3.11+) includes 12 synthetic
text-processing tests: exact source coverage, Unicode/BOM/CRLF, boundary/overlap,
stable retry IDs, empty/invalid/oversized/binary inputs, response bounds and
recovery without content in errors. No cloud, model or private-data access.

From repository root: `./scripts/check.ps1` runs 76 worker tests (three smoke-container cleanup, eight lock/audit, four runner, eight network-policy, eight subtitle, eight extraction-adapter, seven bookmark-passage, ten bookmark, 12 processing
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
No real model export or cloud provider has been exercised.

Version synthetic/approved fixtures, queries, model/runtime versions, hardware and results. Start with >=30 text and >=20 visual/OCR queries as described in MODEL_STRATEGY.md. Measure quality by category, not only aggregate accuracy. Proposed thresholds are not current results.

Native end-to-end flow: install -> cloud setup/sign in -> import -> wait for ready -> search with different wording -> open cited source -> ask question -> restart -> retrieve again -> delete -> verify absent -> sign out. Repeat with user isolation, slow network, quotas and failure recovery. Cloud-provider spending/retention controls require verification before hosted tests.

Choose the native/browser test harness in TASK-011/013. Browser tests alone do not cover Tauri capabilities or local workers. Do not introduce another browser tool to bypass the prior access denial.

## Completion evidence

Record exact commands, passed/failed/not-run results and limitations per task. Review code after tests. Fix material issues before a completion commit. Documentation-only changes require link/state/diff checks, not unnecessary full installer builds.


## Extractor runtime remediation checks

Build both installer target and runtime per services/worker/RUNNER.md, then run
scripts/check_extractor_container.py. Verify exact patched Debian versions, all
96 application versions, absent pip/ensurepip and existing isolation checks.
Installer-only synthetic checksum probe must reject a wrong hash and accept the
correct one. A deliberate 120-second sleep must be cancelled and cleaned up
within 20 seconds, including Windows inherited-pipe handling. A full image rescan
is required after dependency/image edits; open findings remain release gates.
