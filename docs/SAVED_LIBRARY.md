# Saved library restoration

26 October 2026. Local acceptance checks pass. Migration 9 is applied to Gather
after explicit approval; body/grants verified. User signed in as pilot A and
confirmed restoration; the agent observed the hosted list and a metadata-only
refresh. Personal uploads/signup/native connected mode stay gated.

## Flow and contract

Sign in -> memory-only bearer -> POST `/v1/list` -> LibrarySession Auth `/user`
verification -> same bearer calls `public.list_library_sources` -> owned metadata.
Listing never calls inference, claims jobs or retries processing. After refresh,
sign in again; no token/refresh credential is saved in browser storage.

Application input: only `limit` (1..20, default 20), `cursor` (null or base64url,
at most 256 characters). Fixed RPC parameters: `p_limit`, `p_before_created_at`,
`p_before_id`, with no owner argument. Response: `{items, next_cursor}`. Items:
source ID/title/kind/creation time, nullable published and processing version IDs,
existing job ID/state/attempts/safe error code. No originals, passage text,
embeddings, notes, owner IDs or lease capabilities.

## Pagination and authorization

SQL applies `auth.uid()` and `deleted_at is null` on **every page**, even when a
valid cursor was copied from another account. An unsigned cursor is a position,
never authority. Its version-1 JSON contains exactly `v`, `created_at`,
`source_id`. Reject malformed, oversized and unsupported inputs.

Preserve UTC timestamps with six fractional digits; do not round through a JS
Date. Order by immutable created_at DESC, UUID DESC and query `< (time, UUID)`.
Reuse the existing owner-visible index. SQL fetches at most limit+1; the
application validates order, strips lookahead and returns at most 20 items plus
the last returned position. Static pages/ties do not duplicate; a deleted cursor
row remains a valid position. This is not a snapshot across pages: refresh shows
newer sources, and other sessions can make loaded metadata stale. Open/delete
always reauthorize against current SQL state.

## UI and status

The current processing target supplies queued/processing/ready/failed/cancelled.
No target means "not started", never ready. The published pointer is separate:
old published text remains openable during replacement. Unpublished targets have
no Open button. Open retains the exact published-version/citation contract.

Sign-in fetches the first page. Refresh starts over and clears displayed search/
reader data; Load more is explicit. Failed next pages retain their retry cursor.
No background polling/inference. Successful delete removes the row and affected
search/reader data. Single-flight requests, cancellation and session-generation
fences prevent obsolete replies restoring data; account switching clears rows,
results and cursor. Physical cleanup remains the existing separate operation.

## Evidence

- 27 focused Python checks (listing/session/ASGI/actual loopback HTTP), with
  synthetic external identities/repositories.
- 28 real PostgreSQL assertions: copied foreign cursor, tied timestamps/pages,
  anonymous/missing identity, private data exclusion, failed/replacement status,
  exact opening and tombstones. Auth uses an explicit test-only claim shim;
  this is not JWT signature or hosted-session evidence.
- 30 frontend checks include remount/reauthentication, explicit retry, paging,
  published version selection, deletion and cancelled/other-session replies.
- Frontend build/lint/format pass. Production excludes OperatorPilot. Current
  JS/CSS hashes match prior generated native assets and HTML references; no
  native input changed, so reuse the 25 October executable.
- No model requests, cloud capacity changes or protected-container changes.

Run commands separately and inspect each exit code:

```powershell
$env:GATHER_PYTHON = "$PWD/output/asgi-checks/venv/Scripts/python.exe"
.\scripts\python.ps1 -m unittest tests.worker.test_source_listing tests.worker.test_library_session tests.worker.test_library_api tests.worker.test_library_flow_http -q
.\scripts\python.ps1 scripts/check_database.py --listing-only
.\scripts\desktop.ps1 test
.\scripts\desktop.ps1 build
.\scripts\desktop.ps1 lint
.\scripts\desktop.ps1 format-check
```

SQL uses a random, network-isolated 256 MiB task container from the existing
image; only that container is removed. Tool-session Python/Docker access required
escalation, with no installations or shared Docker repair.

User approved `202610260001_source_listing.sql` on `fatolholcjxpwocnpzws`.
Dashboard returned Success. Metadata: body MD5 `bf26531aadd408598381e9e7c43ae5dd`,
empty search_path, SECURITY DEFINER, authenticated execute=true, anon/worker=false.
File SHA-256: `843948cd223c80d8ffff31664f82f5a439ff5966ce868c076ea1b091d2db3d6f`.
Screenshot: `output/library-restoration/hosted-listing-metadata-20261026.png`.
Manual dashboard execution does not populate CLI migration history.

## Hosted UI acceptance and remaining limits

Run `scripts/library.ps1 -Action frontend` and `-Action server` in separate
terminals. At http://localhost:1420/ -> Operator pilot, sign in with an existing
test account. Saved library loads automatically; Refresh saved library makes no
model requests. Actual pilot-A login and restoration are operator-confirmed and
directly observed; clicking Refresh saved library returned the same owned source.
Authenticated layout was inspected. Screenshot:
`output/library-restoration/restored-hosted-library-20261026.png`.

A separate retained Synthetic Gather pilot job
`caae0a28-c50c-4789-9eef-51e62c1fdd7b` reports the stored state processing,
attempts 2/3 and timeout, with no published pointer. This does not prove a worker
is currently active. No Open control is shown; no attempt reset, worker retry,
inference or deletion was performed. The previously completed source remains
cleaned; this retained unfinished job is different.

Hosted B-account/negative-session/pagination matrix and full browser-refresh plus
second sign-in were not separately exercised. Those isolation and remount cases
pass synthetic/local SQL tests, not a new hosted multi-account test. Next:
separately scope real TXT/Markdown selection and privacy/upload gates. Existing
unfinished job recovery needs its own explicit run decision, not an automatic
side effect of listing.
