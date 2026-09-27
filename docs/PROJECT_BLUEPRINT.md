# Desktop knowledge library — project blueprint

## Superseding deployment decision: 27 September 2026

ADR-009 and ARCHITECTURE.md supersede this document's historical local-worker,
local-model, SQLite-queue and zero-recurring-cost proposals below. The current
target is a desktop client with authenticated cloud processing and Supabase Free.
No end-user model downloads are planned. Provider/budget/deployment are deferred;
no paid resources have been created. The ingestion, citation, ownership and
reconciliation requirements below still apply on the cloud service boundary.

Status: supporting detailed blueprint, 26 September 2026. The local desktop preview is built; no cloud service or production release exists. Use PRD.md and ARCHITECTURE.md as the canonical product/architecture entry points, TASKS.md at the repository root for work, and MEMORY.md for current state. PROGRESS.md is historical and includes superseded decisions.

## Product promise

Save content, find it by meaning across documents and photos, and ask questions with verifiable citations. The intended experience is Samsung Gallery-style retrieval extended to PDFs, Word files, presentations and other content. See MODEL_STRATEGY.md for model research and visual retrieval design.

Build Windows first using Tauri, React and TypeScript. Use Supabase Postgres with pgvector for vectors. Keep the existing prototype and personal files intact while the replacement is built in new directories. Existing documents are not automatically uploaded to the cloud.

## First release

- Sign in and access a private document library.
- Import PDF, DOCX, PPTX, TXT and Markdown; keep original files unmodified.
- See queued, processing, ready and failed states with useful retry messages.
- Search by meaning and exact words; see ranked files and matching passages.
- Read extracted text and preview PDFs. Office files initially get an extracted-text preview and original-file download/open action.
- Chat within one selected document, with page/slide/section citations and explicit insufficient-evidence answers.
- Delete a document and its associated stored files, passages and conversations reliably.
- Install on a Windows computer without a developer environment.

Native-text retrieval is the first implementation slice. Photo search and scanned-image OCR are required subsequent slices of the broader product before claiming multimodal search is complete. Audio/video, cross-document chat, collaboration and fully offline AI remain later phases. Until each format is supported, show an honest unsupported-format message.

## Proposed architecture

| Layer | Responsibility | Reason |
| --- | --- | --- |
| React + TypeScript | Library, search, reader, chat and job states | Reusable components and explicit data contracts |
| Tauri | Windows integration, controlled file access and packaging | Native desktop shell around the interface |
| Supabase Auth | User identity and sessions | Shared identity for access policies |
| Supabase Postgres + pgvector | Metadata, passages, embeddings and search | Vectors and permissions in one database |
| Supabase private Storage | Original documents | Recoverable originals, separated from search index |
| Bundled local Python worker | Parsing, embedding, retrieval orchestration and chat | No paid application server; keep heavy work off the UI |
| Model adapters | Embedding and answer providers | Explicit model versioning and replaceable providers |

Budget decision: no recurring paid services. Use Supabase Free and a bundled local Python worker. Generate embeddings locally; run a downloadable local chat model. Benchmark CPU/RAM requirements before selecting models. The desktop ships only public Supabase configuration; local work uses the signed-in user token and RLS, never a service-role key. Shared cloud quotas require server-enforced limits before opening public registration. No paid provider is required or enabled by default.

Use a modular local worker, not microservices. Communicate through bounded structured IPC; avoid an unauthenticated localhost service. Persist the local job queue in SQLite so processing can resume after restart. A closed desktop pauses processing; document that behavior. Native file access and process execution must be restricted to the intended capabilities.

Online behavior: sign-in, sync and vector retrieval require connectivity even though models run locally. Cached reading can follow later. Do not market this as fully local/private-to-device: extracted text, vectors and uploaded originals are stored in Supabase. Explain this in onboarding. Supabase Free currently lists 500 MB database, 1 GB file storage and pausing after one week of inactivity (checked 2026-09-26 at https://supabase.com/pricing). These are shared project limits, not per-user allowances. Set conservative quotas and handle a paused/full service explicitly; no automatic paid upgrades. Revisit Chroma only if cloud constraints prevent the intended release.

## Data and trust boundaries

Proposed entities: documents, document_chunks, ingestion_jobs, conversations and messages. Each owned entity has a user ID. Chunks reference both a document and its owner with constraints that prevent mismatched ownership. Conversations are scoped to one document.

- Enable row-level security on all user-owned tables and private Storage paths.
- Enforce ownership in database queries and search functions, not just interface filters. Prefer security-invoker search functions.
- Validate sessions through Supabase. Local workers are untrusted clients: enforce ownership and quota rules in database functions/policies, not client checks. No privileged database credential is distributed.
- Never put service-role credentials or shared model-provider secrets in React, a desktop bundle, or source control. Public Supabase client configuration is distinct from privileged credentials.
- Do not log document contents, prompts, signed URLs or tokens by default.
- Treat document text as untrusted evidence, never as instructions to execute tools or override system behavior.
- Store session secrets using an appropriate OS-backed credential mechanism; validate the Tauri implementation during authentication work.

## Upload and indexing flow

1. Validate authentication, quota, size and supported format before accepting a file. Proposed initial limit: 20 MB, adjustable after parser profiling.
2. Save the original to a private owner-scoped object path with a generated ID, not a user-controlled filesystem path.
3. Create a durable ingestion job. Record a content checksum and deduplicate within the user's library.
4. Parse in a bounded worker with file, memory and time limits. Preserve page, slide and heading locations. Validate content, not extension alone.
5. Split along meaningful boundaries with token-aware limits and modest overlap. Tune sizes against the selected embedding model; do not hard-code a dimension before selecting it.
6. Batch embeddings and persist every chunk. Record embedding model, dimension and parser/chunker versions.
7. Mark a document ready only after the whole index is committed. Partial/failed documents are excluded from search.
8. Retry transient failures with bounded backoff. Idempotent writes and job leases prevent duplicated passages after a restart.

Storage and database writes are not one transaction. Record states and use cleanup/reconciliation for orphaned uploads. Deletion first hides the document from search, then removes Storage objects and database dependents; retry and verify incomplete cleanup.

## Retrieval and chat

Search combines Postgres full-text retrieval with pgvector similarity, merging ranks using reciprocal rank fusion. Filter by authenticated owner before returning candidates. Group results by document, display actual matching excerpts and retain passage references. Avoid invented relevance percentages.

Use the same embedding model/version for queries and indexed passages. A model change requires a versioned reindex, not mixing incompatible vectors. Start with a measured baseline; add an HNSW index when corpus size and benchmarks justify it. Test filtered recall against exact search.

For chat, retrieve only from the selected document, include bounded recent conversation context, and stream the response. If a follow-up needs rewriting into a standalone query, use the rewritten query only for retrieval. Pass source identifiers to the model and validate cited identifiers against retrieved passages. A valid citation is necessary but does not itself prove an answer is supported; evaluate answer faithfulness separately. Provide cancellation and explicit failure/retry states.

## Efficiency decisions

- Embed once per unique document version; batch and cap concurrent jobs.
- Search on deliberate submit initially; cancel stale requests.
- Paginate the library and retrieve bounded result sets.
- Load document viewers only when opened.
- Keep animation to transform/opacity where practical; no perpetual GPU-heavy backgrounds.
- Limit chat context and output tokens; track cost per indexed document and chat turn.
- Measure before adding caches, extra services or larger models.

Provisional targets, not measured claims: warm search p95 under 2 seconds on a documented connection and 10,000-chunk test corpus; responsive typing while ingestion runs; initial chat feedback immediately and first answer token measured separately. Report UI memory separately from worker/model memory.

## Repository layout to introduce

```text
apps/desktop/          React interface and Tauri shell
services/worker/      Local Python processing and model modules
supabase/migrations/  Versioned schema, policies and search functions
tests/fixtures/       Synthetic, non-personal documents
tests/evaluation/     Retrieval questions and expected evidence
docs/                 Blueprint, design, decisions and progress
```

The root Python files and old data directories remain legacy until a tested migration/import tool exists. No automatic conversion of existing Chroma indexes: rebuild passages from originals after explicit import.

## Delivery checkpoints

| Milestone | Deliverable | Exit evidence |
| --- | --- | --- |
| 0. Foundation | Scope, architecture, design rules and setup inventory | Decisions recorded; unresolved costs visible |
| 1. Desktop experience | Working desktop shell and interactive UI using labelled synthetic data | Library/search/reader/chat navigation, keyboard and reduced-motion checks; Windows build |
| 2. Private storage | Auth, schema, migrations and upload/list/delete | Two-user isolation tests across tables, Storage and search endpoints |
| 3. Real search | Durable ingestion and hybrid search | Full-document retrieval, duplicate/retry tests and retrieval evaluation |
| 3b. Visual search | Photo embeddings, screenshot/scanned-page OCR and mixed-format results | Visual/OCR evaluation, source locations and per-user isolation |
| 4. Document chat | Streamed, source-grounded answers | Scope isolation, valid citations, missing-answer and follow-up tests |
| 5. Release | Installer, onboarding, operational checks and documentation | Clean Windows install and end-to-end flow against staging |

Milestones are sequential quality gates; a pretty prototype is not evidence of real AI functionality. Keep fixture/demo mode visibly labelled until services are connected.

## Testing and release discipline

- Check formatting, lint, types and production builds in CI when a Git remote is configured.
- Unit-test parsing/chunk boundaries and retrieval merge behavior; integration-test database policies and ingestion recovery.
- Build a synthetic evaluation set with at least 30 queries: paraphrases, exact identifiers, late-document passages and absent answers. Proposed initial target: relevant file in top five for at least 90% of answerable queries. Record corpus and model version so scores are reproducible.
- Test cross-user access attempts, wrong-document chat retrieval, deleted documents, duplicates, timeouts and cancelled requests.
- Version migrations and document forward/rollback strategy before applying them. Keep development/staging separate from production.
- Release checklist includes secret scanning, dependency review, signing/distribution decision, backup/restore procedure and smoke tests. These are implementation requirements, not extra permission prompts.

## Learning and communication

At each major checkpoint explain: what we are building, why it is needed, how it works in plain language, what was verified and what remains. Record significant choices as short decision notes. Routine implementation proceeds without repeatedly asking for approval; ask for missing account access, expenses or material product choices when required.

## Decisions still open

- Budget is fixed at zero recurring service fees; validate Supabase capacity and local inference resource usage.
- Local embedding and chat models, chosen after a quality, memory, latency and license benchmark.
- Supabase development project connection and authentication settings.
- Product name, branding and distribution channel. Use a neutral working title meanwhile.

## References

- https://supabase.com/docs/guides/ai/hybrid-search
- https://supabase.com/docs/guides/ai/rag-with-permissions
- https://supabase.com/docs/guides/database/extensions/pgvector
- https://v2.tauri.app/start/prerequisites/
- https://v2.tauri.app/distribute/windows-installer/
