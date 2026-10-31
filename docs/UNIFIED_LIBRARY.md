# One connected Library

31 October 2026. UI integration within the two-account TXT/Markdown pilot.
No new backend, schema, inference configuration or deployment.

## User flow and boundaries

Sign in -> Everything shows owned metadata -> Add file -> local review and
explicit cloud confirmation -> save -> automatic processing -> this same grid
updates -> submit the single semantic search -> open its exact saved version.
Delete requires confirmation, hides the file, and reports completion only after
the existing owned cleanup endpoint acknowledges removal. Pending cleanup remains
visible and retryable. Unpublished sources show metadata/status, never staged text.

App mounts Library.tsx in development and explicit connected builds. There is no
Operator pilot navigation or second sample-search screen in this interface. The
separate default sample-only production build remains labelled fictional. The old
OperatorPilot component is retained only as an isolated regression harness for
manual/synthetic contracts; it is not routed into the connected application.

LibraryWorkspace/LibraryClient remain the shared operation/state contracts.
Backend ownership, publication, limits and citations are unchanged. Session
generations discard late responses; logout clears data and credentials. Typing
and filters are local; only explicit search submits a query. Pagination,
empty-publication checks, uncertain-import replay IDs, metadata-only polling and
attempt-bound recovery retain their limits. Listing never runs inference.

## Direction and provenance

User reference: their mymind Everything screenshot and https://mymind.com/.
Borrow its quiet dark canvas, narrow rail, dominant search, small filter chips
and content-led grid. No copied assets, fonts, branding or proprietary code.
Gather retains locally bundled OFL Manrope and Segoe UI document text. Scoped
tokens: canvas #13161D, surface #1C2029, ink #EEEEE9, muted #A9B1BF, coral #FFAC94
and sage #B7D9BD. No remote assets or new dependencies.

Cards show real filenames/status, not invented thumbnails. Search cards retain
every returned window and character citation. The reader shows plain text on a
warm light surface. Import review and connection details use secondary dialogs
with native focus containment, Escape and focus restoration. Reduced motion
disables transitions. Other formats/bookmarks remain future work.

## Verification and limits

59 frontend checks pass, including five new synthetic HTTP integration checks:
one routed search, reviewed import -> same-grid automatic status, exact opening,
confirmed deletion, replacement truth, restoration, failed-list retry and late
search rejection on sign-out. They prove workflow, not new model quality.
Existing live semantic evidence remains in PRIVATE_DESKTOP_DELIVERY.md.
Frontend typecheck/build, lint, formatting and native rebuild passed; the design
detector reported no findings. Browser review at desktop and 640 CSS-pixel width
showed no horizontal overflow. Live native sign-in/listing restored the two
existing owned files; opening automatic-pilot.md displayed its exact saved text
(including fourteen days). Escape dismissed the reader. These checks submitted
no model request and did not retry/delete the older unfinished source. Final
screenshots/receipt belong under output/unified-library/.
Clean-machine installation, signing and public release remain unverified.

Measured token contrast ratios: body15.55, muted/placeholder8.38, card-muted7.55,
primary-button9.49, selected-filter10.36, reader12.31; input-boundary3.61.
Text pairs exceed4.5:1 and the input boundary exceeds3:1. This is scoped color
evidence, not a blanket accessibility certification. The unsigned installer and
portable app were refreshed. NSIS first hit Windows DLL-loading error623 in the
isolated shell; the same cached packager succeeded in the normal host context.
No Windows setting or dependency was changed to resolve it.
