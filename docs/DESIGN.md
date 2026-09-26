# Design entry point

The governing rules are [DESIGN_AVOID_LIST.md](DESIGN_AVOID_LIST.md); implementation guidance is [DESIGN_DIRECTION.md](DESIGN_DIRECTION.md). Keep those as the single source for detailed design rather than maintaining competing copies.

Current system: local Segoe UI/system sans-serif, warm light surfaces, dark ink, restrained green accent, named spacing tokens, explicit focus feedback and solid controls. No Inter/purple-gradient/template reset from generic guides.

Required screens/states: library, processing queue, search results, reader, selected-source chat, model setup, account/settings and policies. Empty/loading/error/offline/permission/quota states need recovery actions. Only the fixture library, reader, model/policy screens exist today.

Use keyboard-operable controls, visible focus, meaningful labels, reduced-motion support, and preserved reading position. Windows narrow/normal/wide windows and 200% scaling must be checked. Optional Lenis remains reader-only and off by default. Thinking Orbs must not imply work that is not happening.

Before design completion: verify screenshots/native appearance, focus behavior, scrolling, contrast for actual component states and motion preferences. Current visual verification is pending; do not substitute successful compilation for it.
