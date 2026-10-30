# Automatic private text processing

Private two-account pilot only. The connected Windows app and hosted API now pass
the selected native file flow. Clean-install/signing gates remain; see
[delivery record](PRIVATE_DESKTOP_DELIVERY.md).
Reuse the existing Auth, admission, parser, durable jobs, restricted worker,
cloud provider, publication, source listing and deletion contracts.

## Start and scope

```powershell
.\scripts\library.ps1 -Action server -TextFiles -AutoProcess
.\scripts\library.ps1 -Action frontend -TextFiles
```

Requires migrations 10 (`202610270001_automatic_processing.sql`) and 11
(`202610280001_recovery_attempt_fence.sql`), applied to Gather with explicit user
approval. CLI migration history is still not populated automatically.

Migration 12 (`202610310001_owned_cleanup.sql`) adds owner-only cleanup and pending
cleanup listing. It was tested locally, explicitly approved and applied to Gather.

Save a reviewed nonsensitive file -> atomic admission plus automatic intent ->
background exact-job claim -> startup probe under renewable lease -> existing
bounded embedding/staging -> atomic publication -> search/open.

The intent table stores only job ID and requested attempt; it is not a second
job-state ledger. It has RLS enabled with no client policies and no direct client
or worker table grants. Only scoped security-definer functions can access it.
Admission derives the owner from verified Auth. Existing manual jobs are not
enrolled, even if an old import request is replayed in automatic mode.

## Bounds and recovery

- One dispatcher, one existing global DB lease. It wakes on startup, an import
  attempt or accepted explicit recovery; no recurring queue scan or model retry.
- Restart finds committed unclaimed intents. Interrupted/failed claimed work
  requires explicit Resume processing after lease expiry/backoff. The original
  three-attempt ceiling and stale/deleted/superseded publication fences remain.
- Recovery POST `/v1/process` requires source ID, job ID and observed attempt
  (0..2). SQL checks the current owned target and attempt under source/job locks.
  Replayed or stale requests cannot authorize another attempt or a replacement.
- Worker and search share three model attempts per API process. Concurrent
  inference is rejected; failures count. Startup checks do not consume embeddings.
- Startup permits up to three authenticated readiness GETs inside one shared
  60-second allowance (explicit user approval). Only429/503 retry; a cancellable
  helper retains the deadline. It never changes Cloud Run capacity.
  Each embedding still uses its 15-second deadline; leases renew during startup.
- New-import status refresh is metadata-only, at most 30 checks/five minutes;
  it stops on failure, ready, deletion or account switching. Manual refresh
  reads the authoritative state. No browser timer submits an inference retry.
- Server shutdown cancels the active worker and drains bounded work. Closing
  the page only clears its session; it does not undo committed cloud work.

Automatic mode is explicit on the trusted server. A browser flag cannot activate
it. Credentials remain memory-only in the frontend; DB/Google credentials never
enter the client. No new paid service, permanent warming or limit increase.

## Verification and evidence

Local: 83 focused Python checks, including actual loopback HTTP automatic import
with an injected synthetic repository/provider; current frontend54 checks; build, lint
and formatting passed. These fixtures do not establish live semantic quality.
SQL: 23 automatic-intent/recovery checks and 24 existing exact-claim cases pass
in one disposable PostgreSQL container. Coverage includes duplicate submission,
owner isolation, RLS/grants, old-job exclusion, expired lease recovery, stale
attempts, bounded retries and cleanup cascade. Existing publication tests are
reused because publication/storage semantics are unchanged.

Isolated hosted readiness succeeded in 32.62 seconds including 3.59 seconds for
operator identity, with zero embeddings/capacity changes. Earlier five-second
identity attempts failed before reaching readiness; no token was printed.
Receipt: `output/automatic-processing/cloud-readiness.json`.

Final hosted automatic-flow result is recorded in PROGRESS.md and the safe
receipts/screenshots under `output/automatic-processing/` and
`output/operator-pilot/`. The native connected flow is now separately observed;
general-user, full-format and release acceptance remain outside this pilot.

## Owned cleanup and private desktop candidate

`/v1/cleanup` calls the owner-scoped finalizer only after tombstoning. The existing
Storage-object guard must pass; quota releases once and minimal replay receipts
remain. Pending deletions reload after sign-in. An uncertain/failed reply stays
pending and can be retried explicitly. Complete means active application rows,
not provider backups/log erasure. Eleven isolated SQL cleanup checks pass.

Operator tokens reuse the existing memory-only expiry/skew/monotonic cache;
setup may mint within the existing 15 seconds, request refresh stays five seconds.
Inference can wait for the shared outbound slot within its existing deadline,
preventing local rejection during status traffic without increasing concurrency.

Build the private candidate with `scripts/private-desktop.ps1 native`. Its CSP
permits only Gather Supabase and the proposed Gather library HTTPS origin; it
contains the public project key, no DB/Google credential. The API uses managed
metadata identity and two server-side mounted secrets. `scripts/deploy_library_pilot.py`
previews the exact deployment by default; applying it requires separate approval.
The exact new API and two secrets were explicitly approved and provisioned.
The final API image37 synthetic Linux cases pass. The selected native flow supplies
real hosted evidence; see PRIVATE_DESKTOP_DELIVERY.md for its IDs and artifacts.
