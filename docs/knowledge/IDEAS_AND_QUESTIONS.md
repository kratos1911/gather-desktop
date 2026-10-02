---
tags: [gather, planning]
---
# Ideas and open questions

Return to [[docs/PROJECT_HUB]]. Accepted choices are recorded in
[[docs/DECISIONS]]; delivery order and completion evidence belong in [[TASKS]].

## Agreed direction

- Search saved documents, images and bookmarks through one private library.
- Preserve source references so a result leads to the matching passage.
- Keep bookmarks useful with URL and notes when extraction cannot succeed.
- Separate extracted page text from video understanding; a saved video link does
  not mean the video was indexed.
- Use cloud AI without requiring users to download weights. Provider and budget
  are deferred; do independent development without paid calls.
- Follow the existing design system and avoid-list rather than adding effects
  that imply nonexistent processing.

## Deferred

OKF (Open Knowledge Format) is retained as an optional later extension, accepted
2 October: portable knowledge/Obsidian export and linked notes. It does not replace
hybrid retrieval, Supabase, source originals or the later RAG chat pipeline.
Any generated notes require source citations and evaluation for omissions/errors.
Do not implement it before the search foundation. Reference:
https://github.com/GoogleCloudPlatform/open-knowledge-format

Document chat, video/audio indexing, mobile, collaboration, payments and public
sharing are not current search implementation work. Historical model candidates
are proposals, not selected benchmark winners.

## Decisions still needed

| Question | Why it matters | When needed |
| --- | --- | --- |
| Cloud provider, model, tokenizer, spending limit and retention? | Determines embedding quality, dimensions, limits and operating cost. | Before genuine hosted evaluation. |
| Supabase project configuration and user-session design? | Enables private durable libraries and ownership tests. | Before connected ingestion. |
| Initial audience, ages and regions? | Shapes signup and privacy requirements. | Before account collection. |
| Durable queue and API framework? | Needed for retry, cancellation and restart recovery. | Before hosted processing. |
| Parser coverage and real-world extraction quality? | Synthetic HTML tests cannot establish support for all websites. | Before live bookmark release claims. |
| Distribution, signing and operator contact? | Needed for a usable public desktop release and policies. | Before release. |

## Capture a new idea

Use [[docs/knowledge/templates/Idea|Idea template]]. Record the user problem,
example, expected benefit, dependencies, risks and a proposed acceptance test.
An idea is not an approved task until its priority is established. Never put
credentials, private source content or personal information in these notes.
