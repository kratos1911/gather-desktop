# Rebuild progress

## 2026-09-26 — foundation

Completed:
- Inspected the existing PyQt/Python implementation.
- Confirmed user direction: Windows-first desktop, Tauri + React, Supabase vectors, semantic search first and document chat second.
- Wrote project blueprint, delivery gates and interface/motion direction.
- Identified original bugs: first-chunk-only indexing in the desktop path, moving source files, inconsistent metadata, incomplete persistence and stale vectors after deletion.

Environment findings:
- This directory is not currently a Git repository.
- Node reports v22.7.0.
- The currently resolved npm command fails because its npm-cli.js target is missing.
- Rust is not available on PATH or at the standard user cargo location checked.
- Visual Studio Installer exists; the required C++ workload has not been verified.
- Supabase connectivity, credentials and project configuration have not been tested.

No existing source files, original documents, legacy databases or environment secrets were modified. No cloud resources were created and no personal files were uploaded.

Next: resolve the desktop development toolchain, scaffold apps/desktop and build the labelled interactive prototype. In parallel with implementation work, settle the hosting budget and model strategy before introducing a paid dependency. A working Windows installer remains unverified until Tauri prerequisites are available.

Budget update: user requires free operation. Keep Supabase Free for a bounded initial release; revise processing to a bundled local worker and local models. No paid hosting or inference dependency. Verify shared quotas, local hardware requirements and Supabase inactivity behavior before release.

Model research: clarified Gallery-inspired multimodal scope; added MODEL_STRATEGY.md with primary sources and provisional model shortlist. Read development hardware: Ryzen 7 4800H, approximately 16 GB RAM, RTX 3050 Laptop GPU with approximately 4 GB VRAM. No model downloads or benchmarks performed. Photos/OCR are now explicit delivery requirements.

## 2026-09-26 — step 1 implementation

Built the new Tauri + React + TypeScript scaffold in apps/desktop. The working product name is Gather; branding remains provisional. Added a responsive sample library, combined type/text filters, no-results recovery, reader with explicit document scope, disconnected-chat state, and model lineup screen. GSAP entrance transitions respect reduced-motion preferences. All content is labelled synthetic; nothing claims to be semantic search yet.

Toolchain: installed the official Rust stable minimal MSVC toolchain (without modifying global PATH). Verified existing Visual Studio C++ tools. Added scripts/desktop.ps1 to select a compatible installed Node version and bypass the broken npm shim. Installed and locked JavaScript dependencies. Removed the template opener plugin and greeting command; the shell exposes no custom filesystem/shell capabilities. Added a content security policy.

Verification: three component tests passed (combined filters/empty-state recovery, selected-source navigation, and honest unconnected import/model states). TypeScript and production frontend build passed. Initial native Windows compilation passed. Dependency audit reported zero known vulnerabilities at installation time; this is not a security guarantee.

Visual review: the browser tool rejected opening the local preview because permission was declined. No alternate browser or screenshot workaround was attempted. Actual visual appearance, zoom, native interactions and motion remain unverified.

Next checkpoint: review this interface, then add the local processing boundary and a small reproducible embedding benchmark with synthetic text. The four recommended models are accepted starting candidates; no model weights have been downloaded and no Supabase project has been connected.

Final step-1 build: Tauri build --debug --no-bundle succeeded with bundled frontend assets. Executable: apps/desktop/src-tauri/target/debug/gather-desktop.exe. This is a development executable, not a signed installer. Runtime/visual verification remains pending. The temporary browser preview server was stopped.

## 2026-09-26 — design rules and attachment audit

Recorded every user-specified anti-template rule in DESIGN_AVOID_LIST.md, including the interpretation of the two garbled font/texture fragments. Added AGENTS.md so future work reads these rules. Reviewed all seven named design resources; adoption versus inspiration is explicit in the avoid-list resource table.

Implemented Motion-based selected-filter feedback, optional Lenis reader scrolling and a paused, labelled Thinking Orbs example. Removed Lucide and GSAP dependencies, reveal animation, slogan headings, serif heading styles and brightness/fade hover behavior. Added a local original contour SVG, spacing tokens and policy navigation. Main text/button token contrast ratios: 11.95:1, 6.35:1 and 9.30:1; this is not a full-screen accessibility audit.

Read and applied the supplied six-item audit prompt. Added PRIVACY_RELEASE_AUDIT.md with Found / Changed / You still need to for each item and a summary. Added accurate current-state policy screens; production policies and a working copyright report contact remain explicit release gates. No fictitious age gate, unsubscribe, billing or report endpoint was introduced where the underlying feature is absent.

Legacy code changes: removed Google Docs viewer URL requests containing local paths, changed fallback rendering to plain text and redacted dynamic console prints in main.py, main1.py and chroma.py. All three parsed successfully without running them. Data files and environment credentials were not read or changed.

Bundled production dependency license notices in public/THIRD_PARTY_NOTICES.txt. Every installed production package had a license file in the scan. Known-token-pattern source/bundle scan found no matches; this is not an exhaustive secret audit. Dependency installation reported no known vulnerabilities.

Component tests pass (four tests); canvas rendering is explicitly stubbed in jsdom tests and is not visually verified. Native appearance, keyboard navigation, zoom, optional scrolling and orb animation remain pending visual review. Previous browser access denial was respected; no browser workaround was used.

Final verification: all four component tests, TypeScript/frontend build and native Windows build with embedded assets passed after the final policy-footer changes. The existing gather-desktop.exe now contains this update. No cloud services or model downloads were activated.

## 2026-09-26 — TASK-001 structured workflow and version-control baseline

Adopted the user's Read -> Understand -> Plan -> Implement -> Test -> Review -> Fix -> Commit -> Update documentation loop. Added canonical PRD, architecture/design entry points, rules, tasks with acceptance criteria, decision log, current memory, test plan, security requirements and a blank future-public-config .env.example. Updated AGENTS.md and README to use these entry points. Generic Next.js/Vercel/Inter examples did not override the desktop stack or design avoid-list.

Found an existing repository on main with no commits and no remote, and reused it. Explicitly staged the current source, configuration, licenses and documentation as the first recovery checkpoint. Verified 74 baseline paths: no private-data directories, environment secrets, dependencies, model caches or compiled outputs were staged; no file exceeded 1 MB; known secret-token patterns returned no findings; Markdown links resolved. These are bounded checks, not an exhaustive security certification.

Four component tests and the production frontend build passed again. Relevant documentation diff whitespace issues were fixed. The full initial baseline diff reports existing whitespace issues in legacy/template files; no unrelated legacy formatting rewrite was performed. Lint remains unconfigured, native/visual QA remains unverified, and a public repository/remote is not configured. No product runtime changes in this checkpoint, so the prior native build evidence is retained rather than claiming a new native QA run.

TASK-001 is complete in the baseline commit containing this entry. Next: TASK-004 local processing contract using synthetic text only. Audience research, visual review and automated lint/CI remain explicit tasks. Nothing was pushed, published or uploaded.
