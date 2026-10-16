# Security requirements

Inference HTTP local boundary: constant-time service bearer check before body/
inference, fixed loopback binding, bounded headers/body/connections and independent
receive/compute deadlines. This shared credential is NOT user identity or a desktop
secret. No public ingress or Cloud Run IAM verification yet. See INFERENCE_HTTP.md.

Query coordination: only server-created single-user API/provider dependencies are
accepted at the internal boundary. Auth is checked before inference; reader identity,
hashes and citations are validated. Service clients now enforce whole-request
deadlines/body limits and fixed-session read routes; local real-session checks pass.
Inference HTTP authentication, hosted TLS verification and per-user rate limits
remain gates; see SERVICE_CLIENTS.md. No public endpoint or credentials added.

## Trust boundaries

Published search/open RPCs now derive ownership from auth.uid() through PostgREST.
Local real-JWT tests verify signature tampering/anonymous denial and isolation;
this does not close the privileged ingestion connection or hosted-release gates.
Search excludes drafts/deleted sources and incompatible model spaces. Opening
requires the exact current published version. See PUBLISHED_SEARCH.md.

Internal submission now uses a dedicated NOLOGIN coordinator role and derives
ownership from the trusted database session, not an owner field in the payload.
Original handoff bytes and completed-vector IDs are private and lease-fenced.
The DB-API connection factory must configure verified identity and bounded network
I/O; that real transport/authentication boundary remains unverified. See
INGESTION_COORDINATOR.md. No public submission endpoint or new user permission.

Ingestion scheduler: only a trusted coordinator may enqueue verified original
metadata; never pass a client owner/hash as trusted facts. The NOLOGIN worker role
has restricted claim/renew/fail and text/vector staging/publication functions.
Status and published passage reads derive auth.uid() and omit lease tokens.
Publication validates the live lease/target under the same transaction as
activation; staging has no client table grants. See TEXT_PUBLICATION.md.
A database lease fences state writes, not CPU work or in-flight uploads. JWT/API
and upload gates remain open. No client-upload or signup permission was added.

Search-context assembly requires a server-authenticated owner and repository-issued
active snapshots. It verifies supplied owner/version/visibility/hash/offsets and
caps bytes, but is not authentication, RLS or deletion-race protection. Repository
read-time ownership/version/deletion checks remain required before API exposure.

The private inference runtime accepts only trusted engine factories/configuration
and uses an internal Python-serialized pipe. Never expose that pipe or factory
selection to clients. Its request limits and process deadlines do not replace OS
CPU/RAM/PID limits, authenticated ingress, body limits or per-owner quotas. Those
API controls remain pending. The isolated local launcher now verifies Docker CPU,
memory/swap, PID, non-root, read-only and no-network configuration; 18 synthetic
tests pass in the image. It is private stdin/stdout, not authenticated ingress.
Patched candidate image scan now reports 28 open records, including 1 high; see
services/inference/IMAGE_SCAN_REVIEW.md. Deployment remains gated on remediation
and rescan. Licence review remains open. Long requests timed out without OOM;
this does not establish their full-run memory requirements.
The host/container launchers verify model hashes,
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
