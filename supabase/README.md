# Private source schema: preparatory slice

Run `python scripts/check_database.py` with Docker running. The pinned official
PostgreSQL 17 Alpine image may need a first download. The harness creates one
temporary, network-disabled container with no published ports or host mounts;
database data lives in bounded tmpfs and the container is removed afterward.
Trust authentication is confined to that disposable container, never production.

The migration targets Supabase's `auth.users`, `auth.uid()`, `anon` and
`authenticated` contracts. The test-only bootstrap emulates those contracts on
plain PostgreSQL. It does **not** verify Supabase JWT validation, PostgREST,
Auth signup/session handling, Storage, hosted configuration or service-role access.
Do not deploy or connect the desktop yet. Full local Supabase verification remains
TASK-021 work; the smaller harness avoids the full stack on a low-space system disk.

Sources hold file/bookmark metadata; versions hold parser/hash provenance.
Composite foreign keys enforce matching ownership even for privileged writes.
RLS restricts reads/metadata edits; column grants prevent lifecycle/owner edits.
Tombstoned sources and their versions are hidden. Authenticated clients cannot
insert or hard-delete; ingestion quotas and cleanup APIs are not implemented.
No status is advertised as indexed, and there are no vectors or search RPCs yet.
URL shape validation is not SSRF protection and does not authorize fetching.

Nineteen SQL assertions run under actual database roles, covering two users,
missing identity, anonymous denial, metadata validation, ownership/lifecycle
forgery, write denial, composite ownership and tombstone visibility.
Superusers/BYPASSRLS roles bypass row security; never distribute their credentials.
Worker authorization, durable jobs, quota/retry/delete races, Storage policies,
generation publication and end-to-end persistence remain unimplemented.

Design references: [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security)
and [column privileges](https://supabase.com/docs/guides/database/postgres/column-level-security).
