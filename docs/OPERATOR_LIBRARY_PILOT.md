# Restricted operator library pilot

25 October worker update: the exact requested job reached embedding but Cloud Run
returned429/no available instance. Worker mode now reuses the approved scoped
warm/readiness guard BEFORE claiming a job, then restores min0 on exit. Startup
failure consumes no job attempt; inference stays15s. Warming bills during the
bounded run within the existing pilot budget; there is no permanent warm setting.
19 focused tests and frontend build pass; corrected live worker run remains pending.

24 October browser follow-up: sign-in reached the connected screen, but native fetch was incorrectly called as a LibraryClient method. Chrome rejected it before IO. Plain-function wrapping fixes the receiver; real Chrome now reaches the local API with a synthetic invalid bearer. 25 frontend tests/build/lint/format pass. Production assets unchanged; native build reused. Refresh the existing page and sign in again to replace its old in-memory client, then attempt the synthetic import once. No API restart needed; hosted import through the corrected UI remains pending.

24 October 2026. Implementation and local verification complete. Live use of the
new browser screen with hosted credentials remains unverified. The separate
22 October hosted operator-script success remains valid evidence, not proof that
this new UI has passed a live cloud run.

## Milestone status

| Slice | Status and evidence |
| --- | --- |
| Local application HTTP server | Verified: five routes over real loopback HTTP, bounded reads/connections, exact Host/Origin checks, cancellation and shutdown |
| Worker lifecycle | Verified with synthetic dependencies: bounded claims, stop before/after claim and during inference, no late publication after observed stop, saved-vector reuse |
| Desktop transport and workflow state | Verified with synthetic responses: immutable import/retry identity, exact version reads, bounded parsing, late-session result rejection, truthful failure/deletion state |
| Restricted operator screen | Implemented and locally tested; sign-in view visually inspected. Real hosted sign-in/import/search through this UI still needs operator verification |
| Public/native connected product | Not enabled; native packaged build retains sample mode, public signup and personal uploads remain gated |

## Local startup (operator action, not automatic deployment)

Use repository PowerShell. The existing isolated HTTP runtime is reused; no
package install or model download occurs. Temporary files remain under output/.

1. Optional preview of scope, without credentials/network:

   ```powershell
   .\scripts\library.ps1 -Action check
   ```

2. When ready for a real pilot, start the local API in one terminal:

   ```powershell
   .\scripts\library.ps1 -Action server
   ```

   This decrypts existing operator-only restricted DB credentials, obtains a
   short-lived Google caller token using the existing explicitly scoped personal
   account/project helper, and loads only the verified tokenizer. It binds
   127.0.0.1:8765; no cloud resources/settings are created or changed.

3. In another terminal, start the browser development UI:

   ```powershell
   .\scripts\library.ps1 -Action frontend
   ```

   Open http://localhost:1420 and choose **Operator pilot**. The launcher reads
   only the existing public Supabase configuration for the frontend. Sign in
   with one of the two existing synthetic test accounts; never paste passwords
   or access tokens into chat. No signup or arbitrary personal-file selection.

4. Import the fixed synthetic note. Save its displayed source/job IDs. A lost
   response leaves a pending request: use **Retry same import**, which preserves
   the exact request ID and bytes. Do not create another request to bypass it.

5. Run the exact worker command shown by the UI in a separate terminal:

   ```powershell
   .\scripts\library.ps1 -Action worker -JobId <acknowledged-job-UUID>
   ```

   It handles at most one claim, refuses a different job/owner/original and exits.
   An unexpected claim is left for normal lease expiry without processing. No
   automatic polling/scheduler or failure retry is introduced.

6. Refresh status, search the fixed query, open its exact saved version, then
   delete. Record the source ID shown in the cleanup-pending notice. Finalize
   physical cleanup through the existing administrator SQL workflow, then stop
   the API/frontend when finished. Deletion visibility is not physical cleanup.

## Limits and security boundaries

- Application server: loopback only; reviewed Uvicorn0.54.0/h11 0.16.0. At most
  four TCP connections, single active library operation, 5s receive budget from
  TCP acceptance and 5s bounded sends. Auth/DB/inference retain their own limits.
- Browser access: explicitly enabled only for http://localhost:1420 by the
  operator launcher. Preflight allows POST plus Authorization/Content-Type;
  no wildcard origin, credentialed cookies, proxy-header trust or public bind.
- Pilot restrictions: two fixed Auth UUIDs, one exact synthetic note and query.
  Server verifies real user identity; browser validation is not authorization.
  A worker must match the explicit job ID, permitted owner and fixed original.
- Each operator process permits at most three actual inference requests, including
  failed calls. Worker execution and query service have separate process budgets.
  Restarting resets a process budget; this is not an account-wide spend cap.
- Existing pilot-only DB allowances: connect10s inside total15s, SQL unchanged.
  Inference remains15s. Worker mode now uses the scoped warm-capacity guard described above; server mode does not.
  Cloud cold starts may still require diagnosis/readiness checking; do not blindly
  retry the whole flow or leave a warm instance running across manual handoffs.
- Google caller token is not automatically refreshed. Restart explicitly after
  expiry. Supabase browser access tokens are in memory only; refresh tokens are
  discarded. Disconnect clears local state, not server records or other sessions.
- Navigation/reload loses the session-only view. No persistent catalog or refresh
  recovery is claimed. Keep acknowledged IDs until cleanup. There is no automatic
  hosted cleanup worker in this milestone.
- No request bodies/passwords/provider details in application logs. Vite public
  configuration is intentionally publishable; DB and Google credentials never
  enter frontend configuration. Exposed credential rotation remains a release gate.
- Shutdown cancels admitted work. A DB commit that already happened is not undone;
  unknown outcomes still need idempotent lookup/retry. Unobserved process termination
  relies on durable lease recovery, not the local cancellation event.

## Checks performed

- 49 focused Python tests pass (exit0), covering API/session, actual loopback HTTP,
  complete synthetic coordinator flow, ingestion, worker lifecycle and operator guards.
- 24 frontend tests pass (exit0), including sign-in controls, import/status/search/
  open/delete UI sequence, cleanup notice, transport bounds and session-state safety.
- Frontend production build, lint and formatting pass (exit0).
- Native development executable rebuilt with Tauri --debug --no-bundle (exit0):
  apps/desktop/src-tauri/target/debug/gather-desktop.exe. Operator UI is development
  browser-only; no native CSP expansion or production connected mode.
- Signed-out operator screen inspected at normal1280x720 and minimum640x600;
  no horizontal overflow observed, labeled controls and keyboard focus visible.
  Browser error log empty. Authenticated visual/native runtime QA remains pending.
- Existing driver/tokenizer/HTTP imports and launcher preview pass without cloud IO.
- No new live Auth/SQL/inference calls, Docker runs, model benchmarks or deployments.
  Tests use synthetic providers/database fixtures; do not present them as new semantic
  quality, JWT signature, SQL race or production security evidence.

Evidence screenshot: output/operator-pilot/signin-20261024.png (local, ignored).
The sample workspace stays distinct. Stop at this checkpoint; next work requires
an operator live UI acceptance run, then a separately scoped production/real-file
integration milestone with the outstanding privacy/security gates addressed.
