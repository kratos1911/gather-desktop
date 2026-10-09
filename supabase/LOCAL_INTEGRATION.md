# Local Auth, database API and private-file checks

Verified 9 October 2026: **31 HTTP/integration checks**, alongside the separate
49 database assertions/scenarios and 145 existing application tests.

Run `python scripts/supabase_test_stack.py` from the repository with Docker
Desktop running. Requires Python 3.11+ and Docker Compose. The first run may
download the pinned images. No Supabase account, CLI or paid service is required.
Do not run a second copy concurrently. The runner refuses an existing test stack.

The harness starts real Supabase Auth (GoTrue), PostgREST and Storage services
plus Kong on a dedicated Compose network. PostgreSQL 17 uses a bounded temporary
filesystem; Auth and Storage install their own real schemas/migrations. This is
the **core API integration harness**, not the complete CLI/hosted environment:
Realtime, Edge Functions, Studio, pgvector and hosted infrastructure are absent.

Only the gateway publishes a port, explicitly `127.0.0.1:55431`. The database has
no host port. The harness verifies actual Docker bindings before fixture actions.
JWT signing material is randomly generated per run and kept in process memory;
Docker administrators can inspect container configuration. Nothing is logged as
a reusable credential or placed in the desktop. This is not a production setup.
The gateway passes requests through; it does not emulate hosted API-key controls.
Auth and PostgREST validate real JWTs, and Storage enforces database row policies.

Public signup stays disabled. Two admin-created `example.invalid` users sign in,
save sources through the actual RPC endpoint and receive synthetic TXT originals
uploaded through the Storage API. No email is sent, no personal file is read and
no model runs. The users/objects are removed and the test containers/network are
taken down in `finally`; temporary database/file bytes disappear with containers.
A hard process kill can prevent `finally`; the next run refuses leftover resources
so they can be inspected, not silently adopted or deleted.

## Verified flow

1. Real Auth login -> JWT -> owner-derived save RPC and private REST reads.
2. Service fixture upload -> owner download -> cross-user/anonymous/list/public
   denial. Client upload, overwrite and physical delete remain prohibited.
3. Owner delete RPC -> source tombstone and durable cleanup request. Both REST
   and authenticated Storage reads hide the source; another user's file survives.
4. Finalization while Storage metadata remains fails and keeps quota/queue state.
5. Storage **API** removal -> admin read unavailable and object metadata absent.
6. Simulated interruption before finalization -> repeated external removal is
   harmless -> database cleanup releases quota once. Old save retries cannot
   recreate the source. Invalid JWT and public signup are rejected.

## Boundaries still open

The migration creates a private `gather-originals` bucket limited to 64 KiB
TXT/Markdown and an exact `owner/source/original` key. Only reads have a client
policy. This is not a real user upload path: byte/rate quotas, validation,
upload leases and worker authorization must precede enabling client ingestion.

Cleanup ordering is exercised by the integration harness; no deployed background
cleanup worker or scheduler exists. The SQL finalizer checks all remaining object
metadata below the source prefix and fails closed. It cannot prove that a
privileged upload is not in flight. Upload fencing plus orphan reconciliation
must be implemented before production. Never delete `storage.objects` with SQL;
that can leave bytes behind. The test bootstrap's fake metadata tables belong
only to `check_database.py`; this harness uses real Storage migrations and APIs.

Signed-URL revocation/expiry, refresh/logout/secure desktop session storage,
hosted policy/default-grant parity, account erasure, backups and retention,
production image security review, native QA and connected desktop search remain
unverified. No claim of production readiness or complete Supabase coverage.

## Tooling provenance

Compose pins image digests for PostgreSQL 17 Alpine, GoTrue 2.197.0, PostgREST
16.4, Storage 1.79.36 and Kong 2.8.1. Images come from official upstream registries;
their runtime licences remain in the distributions. No third-party source is
copied into application code. Local configuration is based on the upstream
service contracts; production dependency/license/security review remains a gate.

CLI 2.120.0 was explored, checksum-verified (Windows archive SHA-256
`53920013d24bc9e66180f35ceeea9ddc20e65a7afa883421e9c0ba60ad7457ee`).
Its network-default binding published on all interfaces under this Docker setup,
so that stack was stopped and its test volumes/networks removed. The final runner
uses explicit Compose binding and does not require the CLI. Its ignored download
and cached Docker images remain available locally; no global cache was pruned.

References:

- [Supabase local development](https://supabase.com/docs/guides/local-development)
- [Storage schema: treat object metadata as read-only](https://supabase.com/docs/guides/storage/schema/design)
- [Delete objects through the API](https://supabase.com/docs/guides/storage/management/delete-objects)
- [Pinned CLI service configuration source](https://github.com/supabase/cli/tree/v2.120.0/apps/cli/src/commands/start/services)
