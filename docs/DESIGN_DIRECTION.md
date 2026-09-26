# Interface and motion direction

Working concept: a quiet, precise workspace for rediscovering information. Product name remains open.

## Layout

Use a left navigation rail, a central library/search surface, and a document workspace with a collapsible chat panel. Search is the primary action and stays easy to reach. Inside the reader, show the document title and the explicit chat scope: "Ask this document".

Library rows show filename, type, indexing state and import time. Search rows add matching excerpts and page/slide/section references. Clicking an excerpt opens its source location when supported. Avoid a dashboard of decorative metrics.

Import has drag-and-drop and a normal file-picker button. Show per-file progress, supported formats, limits, failures and retry actions. Never claim a document is searchable while processing is incomplete.

## Visual system

Proposed palette: warm off-white canvas (#F7F8FA), white surfaces, dark ink (#18212B), muted slate (#526171), and restrained teal (#087F73) accents. These are starting tokens; verify contrast for each actual foreground/background pair before shipping. Offer dark mode after the core system is stable.

Use a locally available system sans-serif initially, generous text spacing, an 8px spacing rhythm, 12–16px surface corners and subtle borders. Document content gets the largest readable area. Keep file type icons and status colors consistent, with text labels so color is never the only signal.

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
