# Interface and motion direction

Working concept: an expressive, precise workspace for rediscovering information.
15 October: user requested stronger color and typography inspired by GSAP sites.

## Layout

Use a left navigation rail, a central library/search surface, and a document workspace with a collapsible chat panel. Search is the primary action and stays easy to reach. Inside the reader, show the document title and the explicit chat scope: "Ask this document".

Library rows show filename, type, indexing state and import time. Search rows add matching excerpts and page/slide/section references. Clicking an excerpt opens its source location when supported. Avoid a dashboard of decorative metrics.

Import has drag-and-drop and a normal file-picker button. Show per-file progress, supported formats, limits, failures and retry actions. Never claim a document is searchable while processing is incomplete.

## Visual system

Implemented tokens: canvas #F4F6F0, white surfaces, ink #182C29, muted text
#52635E, forest #173D35 navigation/actions, citron #DCF879 selections, coral
#FFB19B secondary artwork and #703426 text on #FFE4D9 preview labels.
The forest sidebar has light text; document surfaces remain light. This is not
a full dark mode. File artwork is fictional and does not imply parsed content.

Self-hosted Manrope (200–800 variable weights, SIL OFL 1.1) provides rounded,
confident UI headings; Segoe UI remains the document reading face. Use the
4/8/12/16/24/32/48px spacing scale, 8px controls, 16px surfaces and 4px labels.
Library uses two columns at laptop widths, three on wide displays, one below
760px. Navigation reflows above content below 480px for zoomed/narrow views.

References visually inspected 15 October: https://gsap.com/ (bold sans scale,
high-contrast green and dark surfaces); https://www.mike-fernandez.dev/ (showcase
entry screen only: expressive color and organic composition); https://guillaumecolombel.fr/
(coral focal color and heavy sans typography). The latter two were discovered
through https://gsap.com/showcase/. No source, fonts or artwork copied from them;
no claim to use their exact font. No GSAP dependency needed for these interactions.

Font source: https://github.com/google/fonts/tree/main/ofl/manrope.
Unmodified TTF and full OFL included in apps/desktop/public/fonts; SHA-256
3ae11c49db0455a3cc33e37d380f20fdb8c7f8b41dc07625c177e3d87a9d6ae6.
Fonts load locally without a runtime font CDN. The search mark is original CSS
geometry; existing fictional file covers were restyled, not downloaded assets.

## Motion policy (updated)

Use the polish of GSAP showcases, adapted to a productivity tool:

- No blanket entrance animation or scroll-triggered section reveals.
- 120–180ms hover/focus feedback and 180–260ms panel transitions.
- Animate selected control backgrounds only when this clarifies the user action.
- Stable streaming chat layout with user-controlled scrolling if the reader has scrolled up.
- Immediate action feedback; motion must not postpone file opening or search submission.

Use CSS for simple transitions and Motion for the selected-filter background. Lenis is opt-in in the reader only; Thinking Orbs is a paused-by-default setup sample until real jobs exist. Respect prefers-reduced-motion. Read DESIGN_AVOID_LIST.md for the governing rules. Avoid scroll hijacking, custom cursors, looping decorative effects and animations on every streamed token.

## Required states and accessibility

Design empty, loading, success, failed, offline, permission-denied and quota-exceeded states for each applicable flow. Provide clear recovery actions. A document without extractable text explains why indexing failed.

All controls need accessible names, visible keyboard focus and predictable focus restoration after dialogs. Escape dismisses overlays. Announce upload/search completion politely; do not announce every generated character. Test at 200% zoom and Windows scaling settings. Use a collapsible pane layout for narrower windows rather than squeezing the document text.

## Prototype review checklist

- Can someone find import and search without explanation?
- Is it obvious which document chat is using?
- Can a citation lead back to its supporting passage?
- Can the user recover from a failed upload or disconnected service?
- Does keyboard-only use work?
- Is the reduced-motion experience complete?
- Is synthetic/demo data labelled and clearly separate from real files?

References: https://gsap.com/resources/React/ and https://gsap.com/docs/v3/GSAP/gsap.matchMedia()/
