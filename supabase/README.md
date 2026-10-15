# Private source schema: preparatory slice

15 October: private durable scheduling now exists; 105 total database assertions
and concurrent scenarios pass. See [ingestion jobs](../docs/INGESTION_JOBS.md) for
limits, role privileges, cancellation and exact gaps. Older statements below
about jobs being absent describe the 9 October checkpoint. No published vectors,
ready transition, actual dispatcher or desktop integration exists yet.

9 October update: real local Auth/PostgREST/Storage checks now pass via
`python scripts/supabase_test_stack.py`. See [LOCAL_INTEGRATION.md](LOCAL_INTEGRATION.md)
for the 31 checks, setup and explicit limits. The desktop remains disconnected.

Run `python scripts/check_database.py` with Docker running. The pinned official
PostgreSQL 17 Alpine image may need a first download. The harness creates one
temporary, network-disabled container with no published ports or host mounts;
database data lives in bounded tmpfs and the container is removed afterward.
Trust authentication is confined to that disposable container, never production.

The migration targets Supabase's `auth.users`, `auth.uid()`, `anon` and
`authenticated` contracts. The test-only bootstrap emulates those contracts on
plain PostgreSQL. It does **not** verify Supabase JWT validation, PostgREST,
Auth signup/session handling, Storage, hosted configuration or service-role access.
Do not deploy or connect the desktop yet. The separate core-service harness now
verifies real API behavior; exact hosted/complete CLI parity remains TASK-021 work.

Sources hold file/bookmark metadata; versions hold parser/hash provenance.
Composite foreign keys enforce matching ownership even for privileged writes.
RLS restricts reads/metadata edits; column grants prevent lifecycle/owner edits.
Tombstoned sources and their versions are hidden. Authenticated clients cannot
directly insert or hard-delete; SQL functions handle quota-aware saves and deletion
requests. These functions are not connected to the desktop or a hosted API.
No status is advertised as indexed, and there are no vectors or search RPCs yet.
URL shape validation is not SSRF protection and does not authorize fetching.

Forty-five SQL assertions and four concurrent scenarios pass, covering two users,
missing identity, anonymous denial, metadata validation, ownership/lifecycle
forgery, write denial, composite ownership and tombstone visibility.
Superusers/BYPASSRLS roles bypass row security; never distribute their credentials.
Worker authorization, processing jobs,
generation publication and end-to-end persistence remain unimplemented.

## Save and deletion transactions (9 October)

`save_source` derives ownership from auth.uid(), locks the owner's quota row,
and atomically saves source metadata, an idempotency receipt and one used slot.
Limits must be provisioned explicitly by trusted administration. No production
limit is chosen. Missing configuration fails closed. A reused UUID request key
returns the same source ID; a different payload with that key is rejected.
Receipts retain owner/key/source ID and payload fingerprint, not source text.
They survive cleanup so old retries cannot recreate deleted sources. Receipt
retention, request-rate/byte/model-cost quotas and account erasure are still gates.
The slot ledger covers sources created through this function; preexisting fixture
rows are unaccounted. A real data migration requires an explicit backfill.

`request_source_deletion` tombstones the source and records cleanup atomically.
Visibility disappears immediately but the slot stays used until cleanup succeeds.
The private `finish_source_cleanup` transaction removes database versions/source
and the queue record and releases the slot once. Failure rolls back all changes.
It is executable only by the migration owner, with no client/worker grant.
The private-originals migration now refuses finalization while Storage metadata
exists below the source prefix. The API test removes actual synthetic originals
before finalization. No background cleanup poller, upload leases or production
external reconciliation exist; concurrent privileged uploads still need fencing.

Version writes lock and check the parent, preventing writes after a tombstone.
Lifecycle functions use quota-then-source lock order. Tests include rollback,
late save/worker retries, distinct/identical concurrent saves, double cleanup and
concurrent derivative-write/deletion. Core local RPC/JWT checks now pass separately;
full hosted/session lifecycle parity remains unverified.

Design references: [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security)
and [column privileges](https://supabase.com/docs/guides/database/postgres/column-level-security).
