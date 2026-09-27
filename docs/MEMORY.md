# Current project state

Updated: 27 September 2026. This is the present-state summary; PROGRESS.md is chronological history and may describe superseded conditions.

## Product and constraints

Gather is a provisional name for a Windows desktop content library with semantic text/photo search and selected-source chat. Tauri/React/TypeScript and Supabase Free remain. User chose cloud AI on 27 September (ADR-009); provider, budget and deployment are deferred. No paid resources authorized/provisioned. No end-user model downloads planned. Design avoid-list applies. No agentic file modification, payment feature or mobile app in MVP.

## Implemented

- Offline TF-IDF keyword baseline and strict scoring harness with corpus/index fingerprints, per-category and per-query metrics. Twenty-one evaluation tests pass. Baseline text-v1 document/evidence Recall@5 is 0.9714 and MRR@5 is 0.8667; 4/5 absent queries return candidates. This is a tiny development comparator, not semantic search or an answerability system.

- Retrieval development corpus text-v1: 14 synthetic documents and 40 queries (35 answerable, 5 absent), with exact evidence mapped to 16 real processing chunks. Seven integrity tests pass. Export tool separates index/query inputs from relevance labels; no model results yet. See tests/evaluation/README.md.

- Transport-independent Python text processor: bounded typed request/results, strict UTF-8 TXT/Markdown, original source offsets, deterministic hashes/versioned passage IDs, structured safe errors. Twelve synthetic tests pass. No filesystem/network/model calls or new dependencies in this module.

- Desktop shell with fixture library, filters, reader, model lineup and preview policy screens.
- Motion selection feedback, optional reader Lenis, paused Thinking Orbs sample, local fonts/artwork/license notices.
- Four passing component tests, passing frontend and native development builds at the last implementation checkpoint.
- Legacy privacy fixes, documented audit and release follow-ups.
- Official Rust toolchain installed; C++ tools found; compatible Node available through scripts/desktop.ps1. Global npm shim remains broken; helper avoids it without changing global PATH.

## Not implemented / unverified

No real desktop import, connected worker/cloud endpoint, embeddings, Supabase project connection, auth, durable search index, chat or signed installer. Processing is tested in isolation, with character-based passages pending tokenizer validation. No native/visual/E2E verification. Previous browser opening was declined; that limitation was not bypassed. Canvas is stubbed in component tests, so passing tests do not verify the orb renderer.

Lint is not configured yet; TASK-011 tracks it. The full initial baseline diff also reports pre-existing trailing-whitespace issues in legacy files; those are not hidden or counted as a clean full-diff check. Git repository: https://github.com/kratos1911/gather-desktop (private). origin is configured; main tracks origin/main. Baseline commit b89ceec was pushed and its remote hash verified. The TASK-001 baseline contains the existing implementation and workflow documents.

## Current task

TASK-005 scorer/baseline checkpoint complete on feature/retrieval-scoring-baseline, based on corpus commit 4cb8e6f. Twenty-one evaluation tests, CLI baseline/saved-run scoring and frontend build pass. Model benchmarking remains partial; no cloud provisioning or personal file access. No desktop/native code changed, so prior component/native evidence is retained, not claimed rerun.

## Next implementation

TASK-005: select provider/model benchmark configuration and build its adapter, then perform tokenizer/embedding evaluation against the frozen baseline. Hosted evaluation/deployment require a selected budget/provider. Add harder long-document and independently reviewed unseen questions before release claims. TASK-002 audience research and TASK-003 visual QA remain open.

## Inputs needed before later gates

Supabase project/public configuration; audience/regions; operator/contact and final policies; cloud provider, budget, model/license/runtime selection; signing and public distribution destination. Do not request secrets in chat. Current .env is private legacy configuration and is not copied into the new app.
