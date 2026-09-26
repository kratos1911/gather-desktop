# Design rules: avoid generic template styling

User requirements recorded 26 September 2026. These rules supersede conflicting suggestions in earlier design notes. Review each screen against this list before calling the interface finished.

## Avoid list

- [x] Purple-to-blue gradients. Use solid neutral surfaces and one restrained accent.
- [x] Gradient hero text. Headings use solid, readable text.
- [x] Emojis in headings. Use plain language.
- [x] Inter everywhere. Use the local Segoe UI/system sans-serif stack for this Windows app.
- [x] Colored left-border cards. Use spacing, labels and subtle full borders.
- [x] Glassmorphism cards. No translucent blur panels.
- [x] Low-contrast dark mode. Dark mode is not implemented; verify contrast before adding it.
- [x] Three icon boxes in a row. Organize actual files and tasks, not decorative feature trios.
- [x] A badge above the headline. Use direct screen titles; preview status belongs in the toolbar.
- [x] Lucide icons everywhere. Removed the dependency and decorative icon repetition.
- [x] Untouched shadcn components. No stock shadcn components installed.
- [x] Sections fading in on scroll. Removed blanket entrance/reveal animation.
- [x] A beam following the cursor. No pointer-following effects.
- [x] Hover effects that fade buttons. Change solid fill/border, preserve text opacity.
- [x] Inconsistent spacing. Use named spacing tokens and documented exceptions for typography/geometry.
- [x] Em dashes throughout interface copy. Use sentences and simple punctuation.
- [x] Generic buzzword copy. Name the task: Your library, Models & setup, Ask this document.
- [x] Serif italics for accent words. No accent-word font tricks; headings now use the UI typeface.
- [x] Space Grotesk / Instrument Serif as the default fashionable pairing.
- [x] Grain textures. No noise overlays or grain assets.

The pasted fragments “Space Groteel nlic Inetriiment Serif” and “Grain textul” are interpreted as Space Grotesk/Instrument Serif and grain texture. The original fragments are retained here so this interpretation is visible. Standalone hyphens are formatting artifacts, not additional rules.

Checked means recorded and addressed in code review, not visually certified. Native appearance, zoom and motion still require visual review; previous browser permission denial remains in effect.

## Positive design direction

A desktop information workspace with strong text hierarchy, readable sources, consistent controls and purposeful movement. Use actual file previews when available. Decorative artwork must remain secondary. Animation represents a user action or processing state; it must not imply a model is running when it is not.

## Resource adoption

| Resource requested | How it is used / disposition |
| --- | --- |
| Aceternity UI | Reviewed file-upload interaction as a reference for the upcoming importer. No source copied and no premium assets purchased; verify component license before reuse. No glowing/3D upload tiles. |
| Lenis | Installed; optional smooth scrolling inside the reader only. Off by default, native scrolling elsewhere, disabled for reduced-motion preference, destroyed on unmount. |
| 21st.dev | Design discovery reference. No marketplace scraping, copied previews or blanket-license assumption. Specific components require license/provenance review before adoption. |
| Jakub Antalik thinking-orbs | Installed; explicitly labelled processing-indicator sample in setup, paused by default. No cursor/gravity feature enabled. Real status wiring follows real jobs. |
| Motion Primitives | Shared-layout selected-background interaction used as a conceptual reference. FilterControl is an original controlled implementation with Motion, no upstream source vendored. |
| Haikei | Reviewed as an SVG composition reference. The local contours.svg is original hand-authored artwork, not claimed as a Haikei export. |
| Realtime Colors | Reviewed palette/contrast workflow. Actual token-pair contrast is calculated locally rather than relying on visual judgment. |

We use compatible ideas and specific tools, not every library's default styling. The user explicitly prioritizes the avoid list over decorative effects those libraries may offer.

## Review gates

- [ ] Actual visual review at normal and 200% zoom.
- [ ] Native keyboard/focus and screen reader checks.
- [ ] Native reduced-motion and optional Lenis behavior.
- [x] TypeScript/frontend compilation.
- [ ] Real ingestion and inference status wiring (later functional step).

Sources: https://ui.aceternity.com/components/file-upload, https://lenis.dev/, https://21st.dev/terms, https://github.com/Jakubantalik/thinking-orbs, https://github.com/ibelick/motion-primitives, https://haikei.app/, https://www.realtimecolors.com/.
