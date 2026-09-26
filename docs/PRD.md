# Product requirements

Status: agreed direction; implementation is still a synthetic desktop preview.

## What and why

Gather (working name) helps people retrieve saved information without remembering filenames or exact wording. The inspiration is Gallery-style natural-language search extended to PDFs, presentations, Word documents, notes, screenshots and photos. A second core outcome is asking questions about a selected source with traceable evidence.

## Users

Initial working audience: individuals using Windows who save study, research and work material across many files. Students and knowledge workers are hypotheses, not validated market research. Recruitment, interviews and competitor comparison remain TASK-002. Audience age policy and launch regions must be decided before account creation is enabled.

## First usable slice

Import one supported text document, see processing status, retrieve a passage by meaning, open its source, and delete it completely. This requires local processing, authenticated Supabase storage/retrieval and ownership enforcement. An isolated model benchmark is a technical prerequisite, not this completed user flow.

## MVP scope

- Windows desktop app and private account/library.
- Native-text PDF, DOCX, PPTX, TXT and Markdown import.
- Photos (initially JPEG/PNG), screenshots and scanned-page OCR as a required second retrieval slice.
- Ranked hybrid search, grouped by source file, with excerpts and page/slide/section/image references.
- File processing states, bounded retries, duplicate handling and safe deletion.
- Selected-document chat with citations, insufficient-evidence answers and cancellation.
- Installable build with explicit model downloads and hardware requirements.

Office preview initially means extracted text plus opening/downloading the original, not guaranteed native-format rendering. Old binary DOC/PPT, spreadsheets, audio/video and other formats must be labelled unsupported until an explicit task adds them. Do not claim universal file support.

## Out of scope

Mobile, payments, public sharing, collaboration, agents that modify files, cross-document chat, video/audio indexing and fully offline search. Do not add these through incidental implementation decisions.

## Acceptance criteria

1. Imports preserve original files and report truthful status.
2. Search retrieves relevant content beyond the beginning of a long document.
3. Photo descriptions and OCR text retrieve actual matching source content.
4. User A cannot list, read, search, chat with or delete user B's content.
5. Chat is scoped to the selected source and citations point to retrieved evidence.
6. Deletion removes search visibility immediately and eventually removes every owned derivative and stored original, with failed cleanup retried.
7. Restart/retry does not duplicate passages or mark incomplete indexing as ready.
8. A clean Windows installation can complete the core flow without developer tools.

Provisional quality targets: text Recall@5 >=90% on a versioned answerable-query set; visual/OCR quality reported separately; warm search p95 <2 seconds on a documented 10,000-chunk corpus/connection. These are targets, not observed performance. Chat latency and RAM/VRAM limits are set after hardware benchmarking.

Budget: zero recurring paid services. Supabase free capacity is finite; local inference consumes user hardware. See MODEL_STRATEGY.md and DECISIONS.md.
