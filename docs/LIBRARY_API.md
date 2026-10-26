26 October: /v1/model-status accepts only {} after the existing user/Origin/Host checks and returns a strict state/used/limit snapshot. Search errors may expose only fixed MODEL_HTTP code/status pairs. No upstream body or automatic inference retry. See MODEL_AVAILABILITY.md.

26 October: sixth POST route /v1/list accepts optional limit (1..20) and cursor (null or base64url <=256 characters). It returns validated owned metadata and next_cursor without inference. Existing admission/CORS/deadlines apply. See SAVED_LIBRARY.md.

24 October update: the internal adapter now has an operator-only loopback server and a restricted development UI. See OPERATOR_LIBRARY_PILOT.md for actual HTTP evidence, scoped CORS, lifecycle and remaining live verification. Earlier no-listener statements below describe the 22 October checkpoint.

# Application HTTP adapter

22 October 2026. Internal ASGI implementation: services/worker/library_api.py.
No public listener, signup, cloud deployment or desktop wiring is enabled.

Trusted create_app composition binds a fresh SessionClient/LibrarySession to each
bearer and cancellation event. Auth verification and authoritative ownership stay
in the existing Auth/PostgREST/database contracts. No owner IDs, credentials,
provider URLs or worker controls are accepted in request payloads.

All seven routes use POST and application/json with one Content-Length:

| Route | Required JSON fields | Optional fields |
| --- | --- | --- |
| /v1/import | request_id (UUID), title, media, content_base64 | source_id for replacement; confirm_cloud_storage (strict boolean, private operator extension) |
| /v1/search | query | limit, integer 1..20 |
| /v1/status | source_id | none |
| /v1/open | source_id, version_id | none |
| /v1/delete | source_id | none |
| /v1/list | none | limit (1..20), cursor |
| /v1/model-status | none (send {}) | none |

Import accepts only existing UTF-8 TXT/Markdown contracts, at most 64 KiB original
bytes / 96 KiB JSON. It returns 202 with the existing durable submission result;
it does not run the worker inline or claim processing completed. Delete tombstones;
physical cleanup remains separate. Open preserves exact source/version binding.
Responses are at most 512 KiB, no-store, nosniff, with fixed safe error codes.
Duplicate/unknown fields, nonfinite JSON, query strings and encoded bodies fail.

One active operation per adapter instance, including body reception. Busy returns
429 without queueing. Body deadline 5 seconds; response wait 30 seconds. Existing
DB/SQL/model limits remain unchanged. Disconnect/timeout sets cancellation;
search and session transport receive it. Admission has existing bounded DB I/O
but is not guaranteed to roll back on disconnect: retry with the same request_id
and check status. The slot stays occupied until the thread really returns.
Cancellation cannot undo a committed import/delete or guarantee remote compute stops.

Verification: synthetic ASGI messages, mock external services and actual
LibrarySession dispatch. They prove routing, validation, redaction, isolation of
bearer routing and cancellation/single-flight behavior; not live HTTP sockets,
JWT signature verification, hosted RLS or semantic quality. Separate hosted pilot
passed with real Auth/DB/cloud vectors; operator confirmed final cleanup=true.

Next: operator-only loopback server composition, actual HTTP integration checks,
and bounded worker lifecycle. Before public deployment/personal uploads: enforce
verified-owner rate limits, deployment-wide capacity, trusted-origin/TLS policy,
server secret packaging, cancellation/shutdown and privacy-release gates. No CORS
or cookie authentication is enabled here. This adapter alone is not release ready.
