26 October: import scope validation now runs after Auth and before admission. Only the trusted PilotSession with TextFiles opt-in accepts confirmed selected-file imports; generic LibrarySession rejects that extension. See PRIVATE_TEXT_FILES.md.

26 October: list_sources verifies Auth on every page and preserves the same bearer for the metadata RPC. Cursors only carry position; SQL independently derives ownership. See SAVED_LIBRARY.md.

# Authenticated library boundary

`services/worker/library_session.py` is an internal application service, with no
public listener, signup route or desktop credentials. Trusted server composition
supplies a SessionClient bound to one bearer token, a restricted admission
repository factory and the existing inference provider.

## Request flow

Import -> Supabase Auth `/user` -> validated owner UUID -> owner-bound admission
repository -> existing submit/queued job. The import method has no owner field.
Repeated requests use the existing durable request ID and database quotas.

Search reuses the existing coordinator, which verifies Auth before inference.
Open, status and deletion verify Auth on every operation, then send the same user
bearer to the existing PostgREST RPC. RLS/SQL ownership remains authoritative;
successful login does not authorize access to arbitrary source IDs. Open requires
an exact source/version pair. Delete creates the existing immediate tombstone;
original/derivative cleanup remains a separate durable operation.

SessionClient adds only two fixed RPC routes: source_processing_status and
request_source_deletion, with exact payload fields and the existing five-second
transport deadline. It still rejects privileged credentials and arbitrary routes.
No identity cache, service-role substitution or new inference limits are added.
Errors crossing this boundary are fixed codes, never raw provider/database text.

## Verification and limits

Unit checks cover forged/unavailable identity before work, owner derivation,
per-operation verification, invalid identifiers and error redaction. The existing
local Supabase harness now runs check_library_session.py with two real local Auth
sessions, actual PostgREST/RLS and the existing ingestion/publication functions.
Embedding vectors are explicitly synthetic. Admission uses a test-only psql
adapter bound to the owner returned by actual Auth; this does not verify a hosted
database driver or its connection deadlines. See TASKS.md for observed results.

The server admission factory is privileged trusted code. Hosted composition must
use fresh bounded connections and the restricted coordinator role, setting owner
context from the verified identity only. Never accept a repository, connection,
factory, owner override or service credential from the desktop. Public signup and
uploads remain gated by PRIVACY_RELEASE_AUDIT.md. No personal files are used here.

Next: concrete bounded production database connection and application HTTP
admission/rate limits, then desktop login/import/search wiring. The prior real
cloud-vector pilot is separate evidence and was not rerun for this change.
