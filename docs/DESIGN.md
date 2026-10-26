# Design entry point

28 September priority: build search first; selected-source chat is deferred.

The governing rules are [DESIGN_AVOID_LIST.md](DESIGN_AVOID_LIST.md); implementation guidance is [DESIGN_DIRECTION.md](DESIGN_DIRECTION.md). Keep those as the single source for detailed design rather than maintaining competing copies.

Current system (15 October redesign): locally bundled Manrope variable sans-serif,
Segoe UI document text, forest navigation, citron selections, coral secondary
highlights and light reading surfaces. Named color/spacing/radius tokens, solid
controls and explicit focus feedback. See DESIGN_DIRECTION.md for provenance
and DESIGN_REVIEW_20261015.md for verified checks and remaining native QA.

Required screens/states: library, processing queue, search results, reader, selected-source chat, model setup, account/settings and policies. Empty/loading/error/offline/permission/quota states need recovery actions. Current code includes the sample library/reader/model/policy screens and a separate development-only operator panel for selected text files, owned listing and model diagnostics. Other general-user screens remain planned; see MEMORY.md for verified scope.

Use keyboard-operable controls, visible focus, meaningful labels, reduced-motion support, and preserved reading position. Windows narrow/normal/wide windows and 200% scaling must be checked. Optional Lenis remains reader-only and off by default. Thinking Orbs must not imply work that is not happening.

Before design completion: verify screenshots/native appearance, focus behavior, scrolling, contrast for actual component states and motion preferences. Current visual verification is pending; do not substitute successful compilation for it.

Planned bookmarks: Save link form with URL and optional title/notes; distinguish
saved, metadata-only and searchable content. Show domain, fetch date and status.
Open original is explicit. Render safe text; failed enrichment keeps the bookmark.
