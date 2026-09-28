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

## ADR-011: source-grounded retrieval development fixtures (27 September 2026)

Use original fictional TXT/Markdown documents with manually authored evidence
quotes. Derive exact offsets/acceptable overlapping chunks through TASK-004
rather than hand-maintaining chunk IDs. Fingerprint source content, questions
and labels; keep expected answers out of model inputs. Distinguish document
retrieval from evidence retrieval and absent-answer behavior. This authored
English development set is not independently reviewed or held out; broader
corpora and visual/OCR evaluation remain required before release claims.

## ADR-012: untuned lexical comparator and strict scoring (27 September 2026)

Use standard-library TF-IDF cosine retrieval as an inexpensive, reproducible
keyword baseline. No query-specific synonyms, stopwords, stemming or label access.
All positive-score chunks are ranked; score document recall after deduplicating
sources, but evidence recall on the first five chunks. Preserve absent queries
outside answerable metric denominators and do not equate candidates with answer
claims. Require complete rankings, valid source/chunk pairs and matching corpus
and processed-index hashes. This comparator is not production retrieval or proof
that embeddings are unnecessary. No provider dependency or paid resource added.

## ADR-013: saved-vector adapter before hosted inference (27 September 2026)

Decouple embedding production from offline comparison using a versioned export.
Validate consistent spaces and complete results before exact normalized cosine
ranking; compare it with TF-IDF and equal-weight RRF (constant 60). Use exhaustive
search for the small evaluation set so approximate-index behavior cannot obscure
model comparisons. Keep all similarity signs; do not invent an abstention
threshold. Tag synthetic vectors explicitly and never report their scores as
model quality. Real provider selection/token checks/usage accounting remain open.

## ADR-014: local quality command and manual CI (28 September 2026)

Use ESLint/TypeScript/Prettier plus the existing Python and UI tests/build in one
local command. Pin added development dependencies and commit the lockfile.
GitHub workflow is manual-dispatch only; authored but not run or pushed. Native
build/QA remains separate. User explicitly controls all pushes.

## ADR-015: bookmarks as library sources (28 September 2026)

User requested links including blogs, gaming sites and Instagram video URLs.
Save URL/notes first and enrich asynchronously; reuse the passage/vector pipeline.
Distinguish bookmark saving, available metadata, extracted page text and actual
video understanding. Inaccessible content remains a useful saved link. Build
synthetic extraction first, then owner-scoped persistence and restricted cloud
fetching. See BOOKMARKS.md for states, SSRF controls and release gates.

## ADR-016: search first and offline bookmark parsing (28 September 2026)

User deferred chat until later. Prioritize source ingestion and search; chat is
not a first-search release gate. Use a bounded standard-library HTML parser for
the initial offline contract, preserving metadata/text provenance and unavailable
states. This is a conservative heuristic, not universal article extraction or an
SSRF-safe fetcher. Real-world parser evaluation and cloud fetching remain pending.
