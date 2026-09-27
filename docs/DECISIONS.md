# Architecture decisions

Recorded 26 September 2026 from this project's existing decisions. Accepted means product/architecture direction, not implemented functionality.

| ADR | Decision | Reason / consequences | Status |
| --- | --- | --- | --- |
| 001 | Windows-first Tauri + React + TypeScript | User selected desktop; retain modern UI and controlled native boundary. Rust/toolchain and installer QA required. | Accepted |
| 002 | Supabase Free, Postgres + pgvector | User preference if free; auth, RLS and vectors together. Shared quotas/inactivity and online search are constraints. Chroma is contingency, not simultaneous backend. | Accepted |
| 003 | Local worker and inference | Original zero-recurring-cost approach; retained for history. | Superseded by 009 |
| 004 | Specialized model pipeline | EmbeddingGemma text, SigLIP visual, PaddleOCR scanned text, Qwen3.5 4B chat/vision. Runtime, versions, dimensions and quantization need measured selection. | Candidates accepted; benchmark pending |
| 005 | Separate embedding spaces + hybrid ranking | Text/image vectors are incompatible; keyword results preserve exact-name lookup. Group by original file. | Accepted |
| 006 | RAG first, no agentic file actions | Core need is reliable search and grounded answers. Model-directed tools/actions remain out of scope. | Accepted |
| 007 | User's anti-template design rules | Local fonts, solid surfaces, restrained interactions. GSAP blanket reveals and Lucide removed. Lenis optional, Motion selection, paused orb sample. | Implemented; visual QA pending |
| 008 | Structured delivery loop and Git checkpoints | User requested documented, small, tested, reviewed tasks through production. Adapt web examples to desktop, preserve the agreed stack. | Accepted |

Change a decision by adding an entry with alternatives, evidence and migration consequences. Do not silently replace accepted choices. MODEL_STRATEGY.md holds candidate research; resource/licensing notes live in DESIGN_AVOID_LIST.md.

## ADR-009: cloud AI, deployment deferred (27 September 2026)

User explicitly chose cloud-hosted AI to avoid end-user model downloads. Desktop
and Supabase Free stay; inference moves behind an authenticated cloud service.
Cloud provider, budget, runtime and queue are not selected and no paid resources
are authorized yet. Prior laptop-based model candidates need cloud cost/quality
evaluation. Shared provider credentials must never enter the desktop bundle.
Uploads/inference require ownership, quotas, retention disclosures and the
privacy release gates before real user content. Local SQLite job orchestration
is no longer the default target; durable cloud jobs will be designed later.

## ADR-010: bounded, transport-independent text contract (27 September 2026)

TASK-004 uses the Python standard library with strict UTF-8 input and exact
Unicode code-point source offsets. Preserve original text rather than normalize
away citation positions. Content hashes and versioned chunk IDs make retries
deterministic, but are never ownership credentials. Start with 64 KiB sources
and 1,024-character passages; actual tokenizer limits are TASK-005's gate.
Do not add an HTTP service, provider SDK or desktop bridge to test extraction.
