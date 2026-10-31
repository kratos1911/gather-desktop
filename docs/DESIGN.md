# Design entry point

28 September priority: build search first; selected-source chat is deferred.

The governing rules are [DESIGN_AVOID_LIST.md](DESIGN_AVOID_LIST.md); implementation guidance is [DESIGN_DIRECTION.md](DESIGN_DIRECTION.md). Keep those as the single source for detailed design rather than maintaining competing copies.

Connected Library (31 October): one authenticated collection/search, quiet dark
surfaces, compact filters and genuine file cards inspired by the user's mymind
reference. Import review and diagnostics live in secondary panels. Tokens,
provenance and checks: [UNIFIED_LIBRARY.md](UNIFIED_LIBRARY.md).

Separate sample-only system (15 October redesign): locally bundled Manrope variable sans-serif,
Segoe UI document text, forest navigation, citron selections, coral secondary
highlights and light reading surfaces. Named color/spacing/radius tokens, solid
controls and explicit focus feedback. See DESIGN_DIRECTION.md for provenance
and DESIGN_REVIEW_20261015.md for verified checks and remaining native QA.

Required states include empty/loading/error/offline/permission/quota recovery. The connected Library now includes owned files, search results, plain-text reading, import review, processing/recovery, cleanup and account/connection panels. Separate sample-only screens remain available only in that build. Chat and other general-user formats remain planned; see MEMORY.md for verified scope.

Use keyboard-operable controls, visible focus, meaningful labels, reduced-motion support, and preserved reading position. Windows narrow/normal/wide windows and 200% scaling must be checked. Optional Lenis remains reader-only and off by default. Thinking Orbs must not imply work that is not happening.

Before design completion: verify native appearance, focus, scrolling, contrast and motion. Connected Library desktop/narrow render and native reader checks are recorded in UNIFIED_LIBRARY.md. Full assistive-technology/native scaling QA remains open; compilation alone is not visual evidence.

Planned bookmarks: Save link form with URL and optional title/notes; distinguish
saved, metadata-only and searchable content. Show domain, fetch date and status.
Open original is explicit. Render safe text; failed enrichment keeps the bookmark.
