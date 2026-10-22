# Bounded PostgreSQL connection

22 October pilot exception, explicitly approved by user: DatabaseRepository keeps
its five-second default and accepts an explicit 15-second trusted override. Only
the supervised hosted pilot selects it. SQL statement/lock/connect settings and
model deadlines are unchanged. Cleanup waits include the selected DB bound plus
one second; Lease accepts at most 16 seconds and otherwise retains six seconds.
Safe SQLSTATE/deadline reasons can cross the private helper boundary; raw messages
and document/credential values cannot. See HOSTED_FLOW_PILOT.md for measured need.

21 October 2026. `services/worker/database_transport.py` composes the existing
PostgresRepository with an actual Psycopg DB-API connection. Local integration
passes. Hosted Supabase configuration, TLS connectivity, deployment and HTTP
application admission remain unverified.

## Ownership and permissions

Trusted server setup constructs DatabaseConfig from secret configuration, never
from desktop request fields. It accepts separate gather_admission/gather_worker
logins (optional Supabase pooler project suffix). The backend gives LibrarySession
an admission factory equivalent to `lambda owner: DatabaseRepository(config,
owner=owner)`. That owner must be the verified Auth result. Worker composition
uses its separate config without an owner.

Admission permits only submit_text. Worker permits only the existing job
operations. Every call gets a fresh connection and transaction; no owner context
is reused. The adapter rejects superuser, RLS-bypass, role-creation, database-
creation and replication privileges on the login. SET LOCAL ROLE selects the
fixed restricted role, and parameterized set_config supplies transaction-local
owner context. Existing SQL ownership, leases, quotas and fencing remain final.
The operator must still review actual role membership/grants before deployment.

## Network and failure bounds

Each operation runs in a separate helper process with a five-second whole-call
deadline, including DNS/connect/query/commit, and up to one second forced cleanup.
Connect timeout is three seconds; existing five-second statement and three-second
lock limits remain. At most two helpers are admitted (operation plus heartbeat).
There are no automatic retries. A timed-out commit can have an uncertain outcome:
reuse the same request ID or let durable lease/status recovery resolve it.

Credentials are passed over private stdin, not CLI arguments, environment or logs.
The helper inherits only Windows system paths, not PG* settings. No arbitrary DSN
or SQL is accepted; requests/replies are bounded to 2 MiB/1 MiB. Native UUID and
timezone-aware lease timestamps are encoded explicitly. Driver details and bodies
are replaced by existing safe repository codes.

Hosted connections require verify-full TLS and an explicit existing CA file.
TLS bypass is available only through an explicit test flag for 127.0.0.1. Neither
hostname/certificate verification against hosted Supabase nor pooler compatibility
was proven by the local test.

## Verification

- Eight new unit/control tests plus existing ingestion/library checks: 24 pass.
  A real stalled subprocess is killed/reaped; configuration, role separation,
  stdin-only credentials, safe failure, TLS settings and lease encoding are covered.
- `./scripts/python.ps1 -m scripts.check_database_transport`: actual Psycopg and
  PostgreSQL, two separate owners, duplicate submission, forbidden replacement,
  staging/embedding/publication, rollback, and privileged-login rejection pass.
  Embeddings and Auth user rows are synthetic; prior real Auth verification is
  recorded separately in LIBRARY_SESSION.md.
- Test database: random task container, 256 MiB, one CPU, temporary data and an
  ephemeral loopback-only TCP port. TCP permits only the two generated password
  logins; no admin TCP access. Container removed after both attempts.
- First integration attempt exposed native datetime results from lease renewal;
  explicit timezone-preserving encoding fixed it. Focused checks and the corrected
  integration pass. Required frontend build passes; UI/native inputs unchanged.

Existing local Psycopg 2.9.9/libpq 16.0 was reused without installing or altering
dependencies. This is local compatibility evidence, not an approved production
dependency set. Pin, hash, license/security review and package a current driver
before hosted deployment. No model calls, cloud writes or protected API changes.

No linked Supabase project/config was found in this checkout; browser inventory
failed before opening a tab. Hosted project existence remains unknown. Next:
application HTTP admission around LibrarySession, followed by operator-approved
hosted configuration and desktop wiring. Public signup/upload release gates remain.

References inspected: [Psycopg DB-API connection parameters](https://www.psycopg.org/docs/module.html)
and [PostgreSQL libpq connection controls](https://www.postgresql.org/docs/current/libpq-connect.html).
