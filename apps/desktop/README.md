# Gather — desktop design preview

Gather is a working name. This first slice contains a React/TypeScript interface in a Tauri shell. It uses fictional fixtures only: no uploads, real semantic search, model execution, Supabase connection or chat answers yet.

## Run from the repository root on Windows

```powershell
./scripts/desktop.ps1 install
./scripts/desktop.ps1 preview
./scripts/desktop.ps1 desktop
```

Use `preview` for the browser development server or `desktop` for the native window. These are long-running commands; stop with Ctrl+C. The preview runs on port 1420. Stop the preview before starting desktop mode because Tauri starts its own frontend server.

The helper selects an available compatible Node executable and avoids broken global npm shims. For a new machine, install Node.js 24 LTS and the official Tauri Windows prerequisites (Rust MSVC, C++ Build Tools, WebView2). Standard `npm ci`, `npm run dev` and `npm run tauri dev` also work with a healthy toolchain.

```powershell
./scripts/desktop.ps1 build
./scripts/desktop.ps1 test
```

`build` validates TypeScript and bundles the interface. It does not build an installer. Native compilation can be checked with `cargo build --locked` from `src-tauri`; the production frontend must already be built. Release packaging belongs to a later checkpoint.

## Code map

- `src/App.tsx`: library filters, reader and model setup screen.
- `src/fixtures.ts`: explicitly fictional files and recommended model descriptions.
- `src/App.css`: responsive visual system and reduced-motion rules.
- `src/components/`: Motion filter selection, opt-in Lenis reader scrolling, paused Thinking Orbs sample and truthful policy screens.
- `public/THIRD_PARTY_NOTICES.txt`: license notices from installed production dependencies.
- `src/App.test.tsx`: navigation, combined filters and honest unconnected states.
- `src-tauri/`: native shell, content security policy and minimal capabilities.
- `package-lock.json` / `src-tauri/Cargo.lock`: reproducible dependency resolutions.

The native shell exposes no custom commands, file access or shell execution. Add capabilities only as a feature requires them. Cloud and model adapters should replace fixture behavior through explicit interfaces in subsequent slices.

