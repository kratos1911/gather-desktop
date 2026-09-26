# Current project state

Updated: 26 September 2026. This is the present-state summary; PROGRESS.md is chronological history and may describe superseded conditions.

## Product and constraints

Gather is a provisional name for a Windows desktop content library with semantic text/photo search and selected-source chat. Tauri/React/TypeScript, Supabase Free and local models. Zero recurring paid-service budget. Design avoid-list applies. No agentic file modification, payment feature or mobile app in MVP.

## Implemented

- Desktop shell with fixture library, filters, reader, model lineup and preview policy screens.
- Motion selection feedback, optional reader Lenis, paused Thinking Orbs sample, local fonts/artwork/license notices.
- Four passing component tests, passing frontend and native development builds at the last implementation checkpoint.
- Legacy privacy fixes, documented audit and release follow-ups.
- Official Rust toolchain installed; C++ tools found; compatible Node available through scripts/desktop.ps1. Global npm shim remains broken; helper avoids it without changing global PATH.

## Not implemented / unverified

No real import, worker, embeddings, model downloads, Supabase project connection, auth, durable search index, chat or signed installer. No native/visual/E2E verification. Previous browser opening was declined; that limitation was not bypassed. Canvas is stubbed in component tests, so passing tests do not verify the orb renderer.

Lint is not configured yet; TASK-011 tracks it. The full initial baseline diff also reports pre-existing trailing-whitespace issues in legacy files; those are not hidden or counted as a clean full-diff check. Working-directory Git repository exists on main with no remote; the TASK-001 baseline commit contains the existing implementation and workflow documents. No GitHub repository was created or pushed.

## Current task

TASK-001 completed in the local baseline commit: workflow documents consolidated, baseline paths reviewed, four component tests and frontend build rerun successfully. No product feature implementation in this checkpoint. Next active implementation selection is TASK-004.

## Next implementation

TASK-004: local text-processing contract and synthetic fixtures. TASK-002 audience research and TASK-003 visual QA remain open; neither may be claimed complete when the worker is added.

## Inputs needed before later gates

Supabase project/public configuration; audience/regions; operator/contact and final policies; model access/license/download setup; signing and public distribution destination. Do not request secrets in chat. Current .env is private legacy configuration and is not copied into the new app.
