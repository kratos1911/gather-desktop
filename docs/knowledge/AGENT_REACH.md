# Agent Reach integration

Historical proposal, superseded later on 30 September 2026 by
[[docs/knowledge/EXTRACTION_STACK]]. Agent Reach is now optional, not the core
extraction toolkit. Never installed, connected or verified in Gather.
Return to [[docs/PROJECT_HUB]] and [[docs/BOOKMARKS]].

## What the upstream project provides

[Agent Reach](https://github.com/Panniantong/Agent-Reach) configures and checks
platform-specific tools. Its [English documentation](https://github.com/Panniantong/Agent-Reach/blob/main/docs/README_en.md)
lists Jina Reader for web-page text and OpenCLI for Instagram using an existing
logged-in desktop Chrome session. These are different runtime and privacy
boundaries; installing the toolkit does not create a production ingestion API.
Reviewed 30 September; actual platform reliability remains untested.

## Proposed Gather flow

1. Validate the submitted URL and save an owner-scoped bookmark with notes.
2. Queue extraction through an explicitly supported, versioned backend adapter.
3. Normalize returned title, text and source metadata; record backend, original
   URL, final URL where available, fetch time and extraction status.
4. Convert page text, metadata and notes into separately labelled passages.
5. Generate real embeddings and commit the searchable version to Supabase.
6. Search the saved passages, returning the original link and matching excerpts.

"Memory" means the user's durable library, not model training or chat memory.
Saving and semantic readiness are separate states. Failure keeps the URL/notes;
it must never label unavailable content as indexed or searchable by meaning.

## Integration boundaries

- Use selected tools behind a narrow worker adapter. Do not run an autonomous
  agent, arbitrary shell commands or the toolkit installer for submitted URLs.
- The existing HTML parser accepts HTML bytes. Jina-style Markdown/text needs
  a separate input adapter; never mislabel it as original HTML or strip it again.
- Public-page extraction comes first. Instagram's documented desktop-session
  path is not enabled for a cloud, multi-user backend. No browser-cookie copying
  or shared operator session. Video understanding remains out of scope.
- External readers receive URLs/content: review disclosure, retention, supported
  access, quotas and licensing before activation. No blanket free/unlimited claim.
- Keep bounded size/time, trusted executable arguments, owner isolation, retry
  and deletion rules. Local URL validation alone does not establish SSRF safety;
  direct fetchers and any selected external reader require separate review.
- Pin a reviewed upstream revision and each enabled dependency before deployment.
  Toolkit branding does not establish the license or behavior of every backend.

## Delivery and acceptance

TASK-018 remains next: offline passage/keyword-search integration.
TASK-019 evaluates an Agent Reach-backed public-page adapter with mocked outputs,
explicit provenance, HTML-versus-text handling, unavailable results, limits and
safe errors. Document each enabled backend and data recipient. Real network tests
follow the existing privacy/fetch gates; provider inference remains deferred.
TASK-017 ultimately joins persistence, fetching, indexing and search.

No Agent Reach package, external account, cookie access, live scraping or cloud
deployment was performed during this documentation checkpoint.
