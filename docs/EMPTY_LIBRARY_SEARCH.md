# Search after the last publication is deleted

26 October 2026. User reported model_unavailable after deleting/cleaning the last
published test file. Actual UI showed only the older unpublished job. Local API
output confirmed the model category; a bounded read of recent failed Gather
Cloud Run request statuses returned no matching rows. The exact dependency
failure remains unconfirmed (including whether a request reached inference).
Do not infer token expiry, cold startup, budget exhaustion or service health.

## Confirmed design problem and fix

Search previously verified Auth and immediately embedded the query, even when
the user had no published content. That unnecessary dependency was confirmed
in source. The coordinator now reuses the existing `list_library_sources` RPC
after Auth and before token counting/inference. Same bearer, no owner argument,
existing strict metadata validation and existing transport/response limits.

One metadata read, at most 21 rows: when the complete page contains no published
pointer, return the normal empty source-neighbors-v1 context. No tokenizer,
Google token minting, model call, ranking or text reads occur. A metadata failure
remains library_unavailable; it is never silently converted into an empty result.

When the lookahead indicates another page, preserve ordinary model search even
if the first page has no publications. This avoids falsely hiding a later
published source and does not add an unbounded pagination scan. The current
two-slot pilot fits the complete-page path. This is deliberately conservative
for future accounts with more than 20 sources; it does not promise zero inference
for every arbitrarily large unpublished library. Listing migration 9 is already
deployed; no migration or new database implementation was needed.

The UI disables Search and explains the empty publication state after a complete
library load. A fresh version-matched ready import also enables search, preserving
the existing Refresh status -> Search flow without requiring a second listing.
The backend remains authoritative even if UI state is stale or bypassed. Failed
replacement processing does not hide an older published pointer. Normal model
errors remain visible whenever inference is actually required.

## Verification and limits

- 41 focused Python checks: search, LibrarySession, ASGI and actual local HTTP
  with synthetic repositories/providers. Cases include empty/queued-only content
  making zero token/model calls; Auth before reads; malformed/failed metadata;
  later-page publication; existing model failure behavior; cancellation; and
  search after deletion making no extra provider calls.
- 18 search checks rerun after the final cancellation fence, all pass.
- 44 frontend checks pass, including disabled empty search without a search
  request; existing ready-import, failed-replacement, open and delete paths.
- Frontend build, lint, format and diff checks pass. Production JS/CSS unchanged;
  existing native artifact reused. No model/Docker/cloud-startup runs, paid
  provisioning, limit increases or document changes.
- Gather-only local API restarted in the same private TextFiles mode. Actual
  pilot-A owned metadata refresh succeeded: the older unpublished note remains,
  Search is disabled with the correct message, and the prior error cleared.
  No live search/inference request was sent for this browser verification.

Evidence (ignored): `output/empty-library-search/before-20261026.png` (user
screenshot), `after-20261026.png` (browser), `verification.json`.

Commands, checking each exit code:

```powershell
$env:GATHER_PYTHON = "$PWD/output/asgi-checks/venv/Scripts/python.exe"
.\scripts\python.ps1 -m unittest tests.worker.test_search tests.worker.test_library_session tests.worker.test_library_api tests.worker.test_library_flow_http -q
.\scripts\desktop.ps1 test
.\scripts\desktop.ps1 build
.\scripts\desktop.ps1 lint
.\scripts\desktop.ps1 format-check
```

This fixes unnecessary inference in the observed empty-publication flow; it is
not evidence of model-service readiness or a diagnosis/fix for every nonempty
model failure. A newly published file can be searched through the existing flow;
do not reimport or reprocess deleted/old jobs merely to test this guard.
