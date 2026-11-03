# Private DOCX body-text import

Status, 2–3 November 2026: implemented, explicitly approved and deployed in the
existing private API. Selected native import -> automatic ready -> real semantic
search -> exact paragraph opening passed. The installed Windows app was updated.
This remains a bounded two-account pilot, not general Office/public acceptance.

## One pipeline, paragraph provenance

DOCX uses the existing authenticated admission, immutable originals, durable
jobs, leases, bounded retries, embedding interface, atomic publication, owned
listing/search/open and deletion/cleanup. No second job ledger or model service.

Parser identity: docx-ooxml-body-v1. Media type:
application/vnd.openxmlformats-officedocument.wordprocessingml.document.
The immutable archive SHA-256 and extracted-text SHA-256 are distinct. Source
offsets are Unicode code points in extracted text. Nonempty main-body paragraphs,
including table-cell paragraphs in document order, receive consecutive extracted
paragraph numbers. Two newlines belong to the preceding paragraph. Empty
paragraphs are omitted. Numbers describe this saved extraction, not Word pages
or original XML paragraph IDs. Word pagination/layout is not reconstructed.

Capture ordinary text runs, tabs and line breaks. Do not index images, OCR,
headers, footers, comments, footnotes/endnotes or drawing/math layout. Reject
fields, tracked changes, text boxes, alternate representations, macros and
embedded active objects rather than returning ambiguous or duplicated text.
Hyperlink labels are plain text; relationship targets are never followed.
The first pilot supports the usual UTF-8, transitional WordprocessingML package
with its main part at word/document.xml; other encodings/packages and legacy DOC
are unsupported. No claim of universal Office compatibility.

## Bounds and trust

- Keep 64 KiB original and extracted text limits and the private three-passage/
  model-attempt budget. At most 128 nonempty extracted paragraphs.
- At most 128 ZIP members, 512 KiB per expanded member and 1 MiB total expanded
  bytes. Read and check actual bytes/CRC without extracting paths to disk.
  Reject duplicate/case-colliding or noncanonical paths, symlinks, encrypted
  entries, unsupported compression, malformed OPC types/relationships and active
  content. Inspect package relationships; never fetch external targets.
- XML is bounded to 20,000 nodes/64 levels per part. Reject DTD/entity declarations
  before parsing; a parser doctype hook also refuses them. No XInclude, schema,
  external entity or template loading. Reject nested paragraphs and alternate
  representations that could duplicate extracted content.
- Auth precedes actual extraction. The pre-auth frame bounds/sniffs only archive
  bytes. A trusted, default-off GATHER_DOCX_PILOT flag controls admission and the
  advertised docx_enabled capability. Browser confirmation cannot enable it.
- PDF and DOCX share one disposable Linux extraction slot: 192 MiB address-space,
  CPU 3s, wall 5s, no core/file output, 32 descriptors and bounded replies. Cancel
  kills/reaps only that helper; its environment contains no DB/model credentials.
  This process/resource boundary is not a general OS network/filesystem sandbox.
- Re-extract the immutable original in the worker and validate hashes, offsets,
  parser/model/version identity. A format-specific staging wrapper calls the
  shared extracted-document validator under existing lease/source locks.
  Preserve old publication during replacement. Staging is private; stale,
  superseded, expired or deleted work cannot publish. Cleanup cascades metadata.

Migration 15, 202611020001_docx_documents.sql, was tested and approved/applied. Private
docx_text stores only extracted-text hash and paragraph ranges. The exact-version
read_published_docx RPC rechecks ownership/current publication. The PDF wrapper
retains its signature and limits; the common staging helper has no client or
restricted-worker execute grant. No public table grants or new RLS policies.

## Desktop and disclosure

Reuse Add file, local review/confirmation, same Library/search, Word filter and
plain-text reader. Archive selection is a local filename/size review, not a fake
extracted preview. Saving discloses original storage in Supabase/Sydney and text
indexing by the existing CPU model/Mumbai. Paragraph citations are rendered as
text and open the exact saved version. Capabilities reset with session/account
state; old servers keep DOCX selection disabled. No redesign or account expansion.

## Verification and delivery

Synthetic fixtures cover Unicode offsets/hashes, runs/tables, archive/XML limits,
active constructs, tampered metadata, pre-auth/gate refusal, job reuse and context
citations. The affected Linux backend run passed 112 checks; the final DOCX subset
was refreshed after parser review. Twenty-two final exact-image PDF/DOCX checks
and pinned-tokenizer composition passed under 512 MiB/1 CPU. Evidence is in
output/docx-pilot/. These check groups overlap; do not sum them as unique tests.

Thirteen isolated SQL groups passed: seven DOCX groups plus six existing PDF
compatibility groups. These use synthetic bytes/identities/vectors; they are not
parser or semantic-search evidence. Checks include complete publication, private
staging, duplicate retries, typed wrappers, owner-isolated search/open, expired
lease recovery, replacement, deletion fencing and cascading cleanup.

Seventy-four frontend checks, lint/typecheck/build and the private native rebuild
passed. New DOCX UI checks use explicit synthetic HTTP/header fixtures; no claim
of native file selection or hosted DOCX success follows from them.

Local artifacts: output/docx-pilot/hosted-pilot.docx (generated nonsensitive file),
Gather-DOCX-Candidate.exe, native-verification.json, staging/image-verification
and Linux runtime receipts. No model was loaded or called during local checks.
No new packages, services, IAM or secrets. The approved per-part correction is recorded below. Existing scanner-open
base-image findings remain; do not infer security clearance from parser tests.

## Approved hosted/native acceptance

The user approved migration 15, image
sha256:9fe1d130274debcfa00fce95e30484871776682caa4fa44d075e043c690493c1
and an update of only gather-library-pilot in Gather/Mumbai. Initial revision 00006-g5r
verified the live flow with DOCX/PDF and the existing performance flags enabled. CPU 1/512 MiB,
min 0/max 1, identities/secrets, model deployment and INR500 allowance are unchanged.
Seven hosted table/RLS/function-grant checks returned true. The browser-entered
SQL matches the tested migration after comment/whitespace normalization; proof
and immutable source hash are recorded in hosted-migration.json.

Both test slots were full. After explicit approval, the app deleted/cleaned only
the generated hosted-pilot.pdf source 9b08bfcd-83b6-4321-b6d5-d046037bb35f. Its local
PDF remains; personal PDF and pilot A's sources were not changed. The new native
window selected the generated 808-byte hosted-pilot.docx, showed local review,
and saved it once after the explicit processing acknowledgement. Automatic
processing reached ready on attempt 1 with no worker command/recovery click.

New source: 3c55a093-daae-4712-afa3-5217917d0bb0.
Job: 05c1f7b6-ea1b-44a1-b58f-22691813d166.
Archive SHA-256: f8a1ef14fafd17e2bb33c0595ee1f1a8d8cbd6256bbd4f8872500647e079541b.
One query, “Where do archive requests belong?”, returned the Cedar queue passage
at extracted code points 0–80, citing paragraphs 1 and 2 because one passage spans
both. Opening it showed the exact saved paragraphs. Word filtering changed only
the displayed results. Cloud HTTP logs confirm exactly two successful /embed
requests: document + query. No inference was replayed. Search is owned-library
retrieval; this is one fixture's success, not broad recall or latency evidence.
The DOCX remains available for inspection; do not resubmit/delete implicitly.
DOCX cleanup is covered by isolated SQL; the real DOCX source was retained.

Native candidate SHA-256:
ceb5fb9506143aea9abb0f394b4fd922d82f10c895f34061ba0056de15feb4b1.
Unsigned installer SHA-256:
89dabc97dfcc5d1c2fc061fca2b1dc910c8a6eccf9f55aff136317b6f550758e.
The existing D: test installation was updated through NSIS /UPDATE, with its
normal shortcut preserved. Installed executable SHA-256:
e4ef7fe97b6fd94587662ff27c44375118de1500120bd2eaddd33c33c6bb5d0c.
All bytes match the verified native candidate except the known Tauri NSIS marker.
Prior artifacts/proof were preserved before promotion. This tests same-version
private update behavior, not clean-machine/cross-version/signing acceptance.
The updated installed executable reauthenticated as pilot B, restored the DOCX
and reopened its exact paragraph reader without another model request.

Safe evidence: live-receipt.json, native-search.png, native-reader.png,
embedding-request-evidence.json, deployment.json, installed-reader.png and installed-update.json under
output/docx-pilot/. Credentials were used only for sign-in and never written to
project files/receipts. Chooser control needed observed File name focus and the
native value setter; failed coordinate/typing attempts did not upload data.
SQL fixture setup and PowerShell framing/date-query issues were corrected without
changing production limits or replaying model requests.

Primary references inspected: [Microsoft WordprocessingML structure](https://learn.microsoft.com/en-us/office/open-xml/word/structure-of-a-wordprocessingml-document)
and [Python ZIP pitfalls](https://docs.python.org/3.13/library/zipfile.html#decompression-pitfalls).

## 3 November compatibility correction

A standard python-docx-produced fixture exposed a legitimate 438,131-byte style
part rejected by the initial 256 KiB member cap. After explicit approval, the
member cap is 512 KiB; total expansion remains 1 MiB, upload/text 64 KiB and all
XML/parser/resource limits remain unchanged. The 826,304-byte expanded fixture
passes the bounded Linux parser and pinned tokenizer with exactly the same body,
paragraphs and model inputs as the live fixture. Final exact-image parser checks:
23 passed. No additional inference was performed.

Corrective image sha256:95bb6106f63623dc90949e34e58359d31ca7974c2478efdcd4a6ab10032e0844
is deployed as gather-library-pilot-00007-x4t. The installed app needs no rebuild.
Evidence: output/docx-compatibility/deployment.json, image-verification.json and
linux-runtime.json. This fixture does not establish universal Word compatibility.
