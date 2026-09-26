# Architecture: how the product works

## Current implementation

apps/desktop contains a React/TypeScript interface, synthetic fixtures, component tests and a Tauri Windows shell. No auth, worker, database client, inference runtime or upload pipeline is connected. Four component tests and a native development build passed in the previous checkpoint. See MEMORY.md for current status.

## Target boundaries

```text
React UI -> typed application services -> narrowly scoped Tauri commands
                                     -> local Python worker (structured IPC)
Local worker -> parsers / OCR / embeddings / chat runtime
Local worker -> authenticated Supabase APIs -> RLS-protected Postgres + pgvector
                                          -> private Storage objects
Local SQLite -> durable job state and restart/retry coordination
```

Supabase Auth supplies user sessions; OS-backed credential storage is to be selected and tested. SQLite is for local job state, not a second cloud vector index. Do not introduce a hosted Python server or public localhost listener without an ADR.

## Architecture rules

- UI components contain no SQL, model execution, filesystem traversal or provider credentials.
- Application services own workflow/state transitions; adapters own external/storage/runtime calls.
- Validate IPC messages, file size/type/content and paths at the native/worker boundary. Treat the desktop client as untrusted for cloud authorization.
- Enforce ownership, quota and resource relationships in Supabase policies/functions. Never distribute a service-role key or database password.
- Text and visual vectors occupy different model-versioned spaces. Fuse result ranks, never raw scores from incompatible models.
- Commit all indexed passages before ready state. Use idempotent writes and bounded durable retries.
- Storage and Postgres operations need reconciliation because they are not one transaction.
- Selected-source retrieval constrains chat; source text is evidence, not executable instructions.
- Run heavy processing outside the interface process; models load on demand with bounded memory and concurrency.

## Layout

Existing: apps/desktop/src/components, fixtures.ts, App.tsx, src-tauri, scripts/desktop.ps1, docs.

Create as needed, not as empty scaffolding: apps/desktop/src/features, services, types; services/worker; supabase/migrations; tests/fixtures; tests/evaluation. Keep fixture mode explicit until each service is real. Preserve legacy root Python files for reference; do not run them against personal documents during checks.

## Release path

Local checks -> development executable -> staging/test installer -> clean-machine QA -> release review -> signed/public installer -> monitoring and iteration. A browser preview is useful UI testing but not proof of native integration. No automatic production publish or remote push is implied by an individual implementation task.

Detailed ingestion design remains in PROJECT_BLUEPRINT.md. This file is the architecture entry point; DECISIONS.md records changes.
