---
tags: [gather, project]
---
# Gather project hub

Start here in Obsidian. Updated 30 September 2026.

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

As of the 30 September cleanup, 70 tests passed (37 worker, 29 evaluation, four UI), along
with lint, types, formatting and frontend build. These checks were rerun after the bookmark passage adapter. Native build previously passed; runtime,
visual verification and remote CI remain unverified.

Implemented building blocks: desktop fixture preview, TXT/Markdown processing,
offline bookmark extraction, TF-IDF baseline, saved-vector comparison and a
mock-tested embedding request client. This is not a working end-to-end semantic
search app yet. Details and evidence belong in the linked state and task notes.

## Immediate next step

Extraction stack accepted 30 September: [[docs/knowledge/EXTRACTION_STACK|Crawl4AI and yt-dlp]].
Agent Reach is optional; tools are selected but not installed or integrated.

TASK-018 is complete: offline bookmark passages and keyword retrieval tests.
Next: TASK-019 Crawl4AI/yt-dlp extraction adapters. Then connect private storage,
restricted fetching and genuine cloud embeddings as their prerequisites become
available. Chat stays deferred. Commit locally; push only on the user's request.

Repository organization: [[docs/REPOSITORY_AUDIT|File-by-file cleanup audit]].
