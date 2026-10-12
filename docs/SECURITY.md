# Security requirements

## Trust boundaries

The private inference runtime accepts only trusted engine factories/configuration
and uses an internal Python-serialized pipe. Never expose that pipe or factory
selection to clients. Its request limits and process deadlines do not replace OS
CPU/RAM/PID limits, authenticated ingress, body limits or per-owner quotas. Those
container/API controls remain pending. The host smoke verifies model hashes,
loads local safetensors without remote model code and uses fictional inputs only.

Treat uploaded content, filenames, model output, desktop clients and IPC messages as untrusted. Protect account tokens, originals, extracted text, vectors, conversations and logs. See PRIVACY_RELEASE_AUDIT.md for concrete findings and release owner inputs.

## Required controls before real data

- 9 October local evidence: 31 real core API checks verify JWT ownership, private
  originals and Storage API deletion before SQL finalization. Public signup and
  client uploads remain disabled. This does not close upload fencing, signed-URL
  retention, worker authorization, hosted parity or production dependency gates.
  See ../supabase/LOCAL_INTEGRATION.md. Never replace Storage API deletion with
  direct SQL writes to storage.objects; absence checks cannot fence in-flight
  privileged uploads by themselves.

- Bookmark enrichment (planned): enforce the fetch boundary in BOOKMARKS.md before
  network access. Reject unsafe schemes, embedded credentials and non-public
  destinations; enforce DNS/redirect/connection checks and egress restrictions,
  bounded responses/timeouts and safe text rendering. Never forward user cookies.
  Treat fetched pages as untrusted evidence; exclude sensitive URLs from logs.

- Cloud inference (ADR-009): authenticate at the API, enforce per-owner request/upload quotas and bounded jobs, keep provider secrets server-side, and define spending limits before provisioning. Decide provider retention/region/logging and disclose document processing before enabling uploads.

- Authenticate sessions; enforce per-owner authorization and quotas in Supabase RLS/functions/Storage policies for every access path.
- Never ship service-role credentials, database passwords or shared inference secrets to the desktop. Store user sessions through a reviewed OS-backed mechanism.
- Give Tauri only necessary capabilities. Avoid arbitrary shell commands or public localhost APIs.
- Validate MIME/content, size, path and parser limits; isolate heavy work. Guard against archive/decompression bombs, malformed documents and resource exhaustion.
- Use generated internal IDs; preserve originals; never interpolate filenames into a shell command.
- Treat retrieved text as evidence, not instructions. Do not let documents trigger tools or cross-user retrieval.
- Enforce idempotent ingestion and deletion/reconciliation across Storage and database state.
- Exclude sensitive values and document content from logs. Telemetry remains absent unless explicitly designed and consented to.
- Pin dependencies/model artifacts; retain licenses and verify downloaded artifacts. No remote font/CDN dependency in the app interface.
- Review backups, retention, export and account deletion before production.

## Repository/release checks

Before commits: inspect explicit staged paths, ignored sensitive directories, suspicious token patterns and diff integrity without printing secrets. Before release: dependency review, two-user adversarial tests, parser/resource tests, permission review, staged-environment QA and the privacy release gates. Pattern scans and vulnerability audits are limited evidence, not proof of security.

Report unresolved findings in TASKS.md/MEMORY.md. No public security-report mailbox has been supplied; do not invent one. Legacy scripts are not a supported production backend and must not be executed on personal data during verification.
