---
tags: [gather, project]
---
# Gather project hub

Start here in Obsidian. Updated 13 October 2026.

Latest: [[services/inference/CONTAINER|Isolated Linux CPU container]] builds on D:
and passes 18 synthetic control tests. Limits: 2 CPUs, non-root/read-only,
network disabled; real-model memory ceiling 5 GiB. The real Qwen container run
is pending the 4 GiB host free-RAM guard, so no new model timing is claimed.
Next: real container smoke, maximum-input measurement and image security review.
Existing API containers are outside this work. See [[docs/MEMORY|Current state]].

Setup update: Docker's disk now runs from D:, verified by full pre-start SHA-256,
active file locking and unchanged 9-container/64-image/1-volume inventory.
Old C: data disk removed after verification; about 36.3 GiB is now free on C:.
Local Hugging Face login works from D:, but that token's account still gets 403
for EmbeddingGemma. Next: bounded CPU serving container on D:.
See [[docs/MEMORY|Current state]] before model/container work.

Newest verification: real persistent Qwen host smoke now passes. Startup 14.24 s,
three requests 0.51–0.71 s; same process reused and cleanly stopped. Post-request
RSS 2.54 GiB, not peak. Docker disk migration is now complete; Gemma access is denied.
See [[services/inference/README|Serving evidence and remaining gates]].

Newest: [[services/inference/README|Persistent CPU serving prerequisite]].
Process reuse, input/token limits and actual timeout cleanup have 14 synthetic
checks; 169 total tests and frontend quality/build checks passed on 12 October.
Docker storage migration from C: to D: is verified. Hugging Face login
works; Gemma terms acceptance/access must match the token's account. Container runtime remains unverified.

Latest: [[docs/TEXT_V2_RESULTS|Fresh text challenge and failure review]]. Forty
new sources and 64 questions are frozen; real Qwen 512 passes the development
gate with 100% document recall and 99.11% evidence recall. Exact-code/temporal
ranking and a missed multi-part passage remain open. 39 evaluation tests and
frontend build pass. Next: a local serving container with explicit resource limits.

10 October checkpoint: [[docs/CPU_BENCHMARK|First real Qwen CPU benchmark]] is verified on D:.
All 35 answerable development queries have relevant documents in the top five;
the set is too small to choose a production winner. Four-thread warm median
0.324 seconds; sampled peak RAM 3.58 GiB. 150 tests and frontend build pass.
EmbeddingGemma terms are now accepted; local access/runtime remains unverified.
Visual/OCR and chat are not tested.

Docker recovery is verified: hash-locked build and offline checks pass. Current
security gate: the 8 October scan reports 29 records, including two high.
Package versions are unchanged this turn; scan/feed changes are not new code
fixes. TASK-023 remains partial after earlier OpenSSL/PCRE2 and installer fixes.
See [scan review](../services/worker/IMAGE_SCAN_REVIEW.md). Source quality checks
cover 145 tests. OKF remains a later optional export idea (ADR-029).

[[docs/DELIVERY_PLAN|Current delivery and system design plan]] explains the target
architecture, flows, security tests and next tasks. TASK-023 retains unresolved
security gates. TASK-019B transport and offline supervision pass controlled tests;
Whole-fetch deadlines and controlled fetch-to-parser integration now pass.
Production confinement and browser/tool egress remain open. See
[[services/worker/SUPERVISION|Verified worker boundaries]].

[Explorable target architecture](../.archify/architecture-gather-plan-20261002-081351/gather-plan.html)
has nine passing structural checks and verified plan references; browser/visual
review was not performed. Save/search flow diagrams are inside DELIVERY_PLAN.md.

## Goal and present focus

Find saved files and links without remembering their names or exact wording.
Search first; document chat is deferred. Desktop: Tauri + React + TypeScript.
Cloud AI is planned on Google Cloud Run, CPU first; Supabase Free is the intended
vector backend and R2 stores originals. The user created a Google Cloud account.
No deployed app/inference endpoint is verified. The local benchmark is separate.

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

As of 8 October, 145 tests passed (112 worker, 29 evaluation, four UI), with lint,
types, formatting and frontend build. Locked-image smoke and timeout cleanup pass.
Native build previously passed; visual verification and remote CI remain unverified.

Implemented building blocks: desktop fixture preview, TXT/Markdown processing,
offline bookmark extraction, TF-IDF baseline, saved-vector comparison and a
mock-tested embedding request client. This is not a working end-to-end semantic
search app yet. Details and evidence belong in the linked state and task notes.

## Immediate next step

The broader frozen text set is measured. Continue TASK-005 with a bounded
serving-container test before committing to model dimensions, fusion or cloud sizing.
[[docs/CPU_BENCHMARK|Benchmark method and evidence]] explains dense retrieval,
dimension reduction, timings and their limits. Local downloads are on D: only.

TASK-021 now has 49 database checks plus 31 real Auth/PostgREST/Storage checks;
see [[supabase/LOCAL_INTEGRATION|Local API verification and limits]]. Private
original access and API deletion before SQL finalization pass. The disposable
stack is removed after checks; desktop persistence is not connected. Next: upload
fencing, background reconciliation and job leases.
[[docs/knowledge/SEARCH_CONCEPTS|Concepts]] explains the cleanup ordering.

Extraction stack accepted 30 September: [[docs/knowledge/EXTRACTION_STACK|Crawl4AI and yt-dlp]].
Agent Reach is optional; selected tools are installed in the offline Docker image,
but live invocation and desktop integration remain pending.

TASK-018 is complete: offline bookmark passages and keyword retrieval tests.
TASK-019 offline runner and container smoke checks pass; next are dependency remediation,
public-only network enforcement and actual extraction execution. Then connect private storage,
restricted fetching and genuine cloud embeddings as their prerequisites become
available. Chat stays deferred. Commit locally; push only on the user's request.

Repository organization: [[docs/REPOSITORY_AUDIT|File-by-file cleanup audit]].
