# Private Windows/cloud delivery

31 October 2026. Current two-account TXT/Markdown pilot, not a public release.

## Delivered and observed

1. Automatic ingestion: native file selection/review/Save created an owned durable
   job and reached ready on attempt 1. No local worker command was used.
2. Recovery/deletion: a previously queued synthetic source recovered under its
   existing attempt ceiling, passed search/open, then app deletion confirmed
   physical cleanup after explicit approval. Pending cleanup is restored from
   owned metadata and retryable without manual SQL.
3. Windows/cloud: built the private executable and unsigned NSIS installer.
   Verified hosted sign-in, fresh Save -> automatic ready -> custom semantic
   search -> exact saved text on the current Windows machine. Stopped both
   localhost helpers and reloaded the owned library successfully from the cloud.
   Clean-machine install/uninstall and release signing are still unverified.

The retained native fixture is 133 UTF-8 bytes, source
`88da1cf6-3708-4f07-9631-6493601a3f3a`, job
`3cdff172-3ad8-4cb4-a0ac-01fd651dbd27`, version
`d95dbd59-9e9c-4bfc-9167-29a2689c8dfe`. Admin metadata independently reports
ready/attempt1/Qwen. Query: "How long are the Orchard team's backups retained?"
The real cloud result contains "fourteen days" with citation code points 0..133.
It remains available for inspection; never rerun/delete it implicitly.

The generated earlier source `f092452e-6a08-47a3-92eb-d75153bd4d00` was cleaned
through the app after explicit approval. The protected older job
`caae0a28-c50c-4789-9eef-51e62c1fdd7b` still shows processing/attempt2/timeout;
it was neither retried nor deleted. Stored status does not prove a live worker.

## Runtime and security boundaries

- API: `gather-library-pilot`, Gather project `gather-development-511211`, Mumbai,
  CPU1/512MiB, max1/min0; platform concurrency4, app admission1, outbound slot1.
- Model: existing private `gather-inference-pilot`, CPU2/5GiB, concurrency1/max1/min0,
  pinned Qwen revision and 512 dimensions. No end-user model download.
- Actual API unauthenticated POST returns401; native-origin preflight returns204.
  Every operation verifies Supabase identity and the fixed two-user allowlist;
  SQL/RLS enforce ownership/version constraints independently.
- Two existing restricted DB passwords were transferred, after explicit approval,
  into Mumbai-replicated `gather-library-admission`/`gather-library-worker` secrets.
  Only the approved runtime identity has accessor grants on those secrets.
  The client contains only public configuration; no DB/Google credential is bundled.
- Migrations 10/11/12 were tested, approved and applied manually. Never blindly
  push migrations based on an empty CLI migration-history table.
- Three model attempts per API instance; two source slots per test account;
  64 KiB/three-passage inputs. These are pilot controls, not billing meters.
- User approved up to three readiness GETs inside one shared 60s budget. Only
  startup429/503 can retry; inference remains15s with no automatic replay.
- Both services scale to zero. The existing aggregate INR500 pilot allowance and
  alert-only budget remain; there is no guaranteed billing hard cap or cost claim.

## Checks, artifacts and reproducibility

Focused changed-behavior backend/HTTP checks pass; 54 frontend tests,
typecheck/lint/format pass. Owned-cleanup SQL11 cases pass; prior automatic/exact
claim SQL47 cases are retained. Final Linux API image37 cases pass with synthetic
providers. Fixtures prove workflow/security behavior, not live retrieval quality.
The selected native fixture supplies separate real hosted semantic-flow evidence.

Final API image:
`sha256:522826fd030d34807e17c2073c1b23d8376a30d215d936f738e74f83a4cc3724`.
The full initial high/critical scan found filelock and zlib. Filelock4.2.1 was
hash-verified against PyPI and its actual image package rescanned with no high/
critical finding. The scanner-open zlib entry is retained; its binary hash exactly
matches the previously regression-verified backport. No suppression or blanket
image approval is claimed. See `services/inference/zlib/README.md`.

Build: `scripts/private-desktop.ps1 native`. Package the verified executable:
`scripts/private-desktop.ps1 installer`. Installer bundling uses an isolated copy
to avoid mutating a running binary. Tauri's documented `useLocalToolsDir` keeps
downloaded tool caches in the D: target directory:
[Tauri configuration](https://v2.tauri.app/reference/config/#uselocaltoolsdir).

Local artifacts (ignored, not GitHub releases):

- `apps/desktop/src-tauri/target/debug/gather-desktop.exe`.
- `output/private-desktop/Gather-Private-Pilot.exe` (same verified executable).
- `output/private-desktop/installer-target/debug/bundle/nsis/Gather Private Pilot_0.1.0_x64-setup.exe`.
- `output/milestone-delivery/`: selected browser/native screenshots and safe receipt.
- `output/library-image/`: verification, dependency scans and safe deployment steps.
- `output/library-upload-receipt.json`; no secret values or access tokens.

The first bundle attempt hit the running-executable file lock. The isolated-copy
bundle succeeded without closing the user's app. No installer was run, no model
benchmark was repeated, and no unrelated project/container was changed.
