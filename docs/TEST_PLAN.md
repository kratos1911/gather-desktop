# Verification plan

## Current executable checks

From repository root: `./scripts/desktop.ps1 test` runs four React component tests. `./scripts/desktop.ps1 build` checks TypeScript and builds frontend assets. Use the documented Tauri build for native changes. Lint/format enforcement and CI remain TASK-011; do not report them as passed yet.

The four tests cover combined filters and empty recovery; selected-source navigation; honest disconnected import/model state; accurate privacy/copyright navigation. jsdom cannot prove browser/native rendering, GPU performance, accessibility or inference.

## Planned feature checks

| Area | Required cases |
| --- | --- |
| Worker/extraction | Empty/malformed/oversized/unsupported input, stable locations, all document sections, safe errors |
| Ingestion | Restart, retry, duplicate content, partial failure, missing source, quota, bounded concurrency |
| Auth/access | Signup policy, login/logout/expiry, wrong credentials, two-user denial on every file/chunk/chat/storage/search path |
| Retrieval | Paraphrases, exact identifiers, late-document passages, no-answer queries, owner filtering, model-version mismatch |
| Photos/OCR | Visual descriptions, rotation/small text, confidence, separate-space fusion, source locations |
| Chat | Selected-source isolation, follow-ups, grounded citations, absent evidence, prompt injection, cancellation and timeout |
| Deletion | Immediate exclusion, all derivatives removed, Storage failure retry, restart during cleanup |
| UI | Loading/empty/error/offline states, keyboard/focus, screen reader labels, reduced motion, narrow windows and 200% scaling |
| Installer | Clean Windows machine, first-run downloads, update, uninstall/data choice, no Python/dev tools required |

## Evaluation and E2E

Version synthetic/approved fixtures, queries, model/runtime versions, hardware and results. Start with >=30 text and >=20 visual/OCR queries as described in MODEL_STRATEGY.md. Measure quality by category, not only aggregate accuracy. Proposed thresholds are not current results.

Native end-to-end flow: install -> setup/sign in -> import -> wait for ready -> search with different wording -> open cited source -> ask question -> restart -> retrieve again -> delete -> verify absent -> sign out. Repeat with user isolation, slow network and failure recovery.

Choose the native/browser test harness in TASK-011/013. Browser tests alone do not cover Tauri capabilities or local workers. Do not introduce another browser tool to bypass the prior access denial.

## Completion evidence

Record exact commands, passed/failed/not-run results and limitations per task. Review code after tests. Fix material issues before a completion commit. Documentation-only changes require link/state/diff checks, not unnecessary full installer builds.
