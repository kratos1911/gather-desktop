---
tags: [gather, project]
---
# Gather project hub

Start here in Obsidian. Updated 3 October 2026.

Docker recovery is verified: hash-locked build and offline checks pass. Current
security gate: 31 scan records remain open after verified OpenSSL/PCRE2 patches
and removal of runtime pip/ensurepip. TASK-023 remains partial (four high findings).
See [scan review](../services/worker/IMAGE_SCAN_REVIEW.md). Source quality checks
cover 109 tests. OKF remains a later optional export idea (ADR-029).

[[docs/DELIVERY_PLAN|Current delivery and system design plan]] explains the target
architecture, flows, security tests and next tasks. TASK-023 retains unresolved
security gates; TASK-019B local isolation work can proceed without live fetching. Proposed mechanisms are not live implementation.

[Explorable target architecture](../.archify/architecture-gather-plan-20261002-081351/gather-plan.html)
has nine passing structural checks and verified plan references; browser/visual
review was not performed. Save/search flow diagrams are inside DELIVERY_PLAN.md.

## Goal and present focus

Find saved files and links without remembering their names or exact wording.
Search first; document chat is deferred. Desktop: Tauri + React + TypeScript.
Cloud AI is planned; Supabase Free is the intended vector backend. No provider
account, paid resources or live inference is connected.

## Navigate the project

| Question | Authoritative note |
| --- | --- |
| What works now? What remains unverified? | [[docs/MEMORY|Current state]] |
| What is done and what is next? | [[TASKS|Delivery board and acceptance criteria]] |
| What happened, and what was tested? | [[docs/PROGRESS|Work journal]] |
| What are we building? | [[docs/PRD|Product requirements]] |
| How will the parts work together? | [[docs/ARCHITECTURE|Architecture]] |
| Why did we choose this approach? | [[docs/DECISIONS|Decision record]] |
| What do the techniques mean? | [[docs/knowledge/SEARCH_CONCEPTS|Search concepts]] |
| What ideas are agreed or still open? | [[docs/knowledge/IDEAS_AND_QUESTIONS|Ideas and open questions]] |
| How should it look? | [[docs/DESIGN|Design]] and [[docs/DESIGN_AVOID_LIST|Avoid list]] |
| How will we verify and protect it? | [[docs/TEST_PLAN|Tests]], [[docs/SECURITY|Security]], [[docs/PRIVACY_RELEASE_AUDIT|Release gates]] |
| How are bookmarks handled? | [[docs/BOOKMARKS|Bookmark specification]] |
| How should these notes be maintained? | [[docs/knowledge/OBSIDIAN_WORKFLOW|Obsidian workflow]] |

Open [[docs/knowledge/Search flow.canvas|Search flow canvas]] for the visual map.

## Latest verified development checkpoint

As of 3 October, 109 tests passed (76 worker, 29 evaluation, four UI), with lint,
types, formatting and frontend build. Locked-image smoke and timeout cleanup pass.
Native build previously passed; visual verification and remote CI remain unverified.

Implemented building blocks: desktop fixture preview, TXT/Markdown processing,
offline bookmark extraction, TF-IDF baseline, saved-vector comparison and a
mock-tested embedding request client. This is not a working end-to-end semantic
search app yet. Details and evidence belong in the linked state and task notes.

## Immediate next step

Extraction stack accepted 30 September: [[docs/knowledge/EXTRACTION_STACK|Crawl4AI and yt-dlp]].
Agent Reach is optional; selected tools are installed in the offline Docker image,
but live invocation and desktop integration remain pending.

TASK-018 is complete: offline bookmark passages and keyword retrieval tests.
TASK-019 offline runner and container smoke checks pass; next are dependency remediation,
public-only network enforcement and actual extraction execution. Then connect private storage,
restricted fetching and genuine cloud embeddings as their prerequisites become
available. Chat stays deferred. Commit locally; push only on the user's request.

Repository organization: [[docs/REPOSITORY_AUDIT|File-by-file cleanup audit]].
