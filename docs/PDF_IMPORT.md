# Private native-text PDF import

31 October 2026. Adds PDFs to the existing owned import/job/publication/search
pipeline. Restricted to the same two accounts and nonsensitive test files.

## Contract

- Keep the original PDF bytes and SHA-256. Store extracted text with its own
  SHA-256, pinned parser `pdf-pypdf6.21.4-text-v1` and contiguous numbered page
  ranges in Unicode code points. Text offsets refer to extracted text, not PDF
  byte positions or visual coordinates. Do not normalize or truncate to fit.
- Preserve the 64 KiB input limit, 64 KiB extracted-text limit and three-passage
  pilot budget. At most20 pages; every page must contain selectable text. Reject
  encrypted, empty/scanned-page, malformed and over-limit PDFs before admission.
  No OCR, image indexing, form filling or original-page rendering is implemented.
- Selecting a PDF reads bounded bytes locally and shows filename/size and a
  disclosure, not a fabricated extracted-text preview. Explicit confirmation
  sends the original to Supabase/Sydney. Only extracted passage text goes to the
  existing private CPU model in Mumbai. No local model download.
- Parse after verified Auth. The framing validator only bounds/sniffs bytes.
  The trusted session validates and counts actual extracted text before creating
  an idempotent job. The worker re-extracts the immutable original under lease,
  checks raw hash/length/parser/model, stages text/pages/vectors and publishes
  using the existing atomic publication fence. Replacements retain old publication;
  deletion and lease loss prevent late publication. Existing retry limits apply.
- Migration13, `202610310002_pdf_documents.sql`, adds PDF media to the existing
  job contract and private `pdf_text` provenance. No direct client/worker table
  grants or RLS policies. Worker has only stage_pdf; authenticated page reads
  require the exact currently published owned source/version. Cleanup cascades.
- Search retains raw source identity and verifies extracted-text SHA separately.
  Context windows carry every overlapping page number; opening preserves version
  and shows numbered extracted pages. Do not silently open a replacement.

## Bounds and dependency provenance

pypdf6.21.4, BSD-3-Clause, official PyPI wheel SHA-256
`33e4fb41ca352810eb4e9838aa0d82d6888a5f8bf682f43e99cce5faa666255c`.
Lock: services/worker/requirements-pdf.lock. The wheel's license/dist-info remain
in the image. Local Python3.10 tests additionally need pinned typing_extensions;
the Cloud Run Python3.12 parser does not need that conditional dependency.

The production parser is a disposable Linux process: one extraction slot,
192 MiB address space, CPU3s, wall5s, no core/file output,32 file descriptors,
256 KiB stream decoding limit and bounded replies. Cancellation kills/reaps its
own process; no credential environment is inherited. This is not an OS filesystem/
network sandbox. The pure-Python reader does not execute PDF scripts or follow
links; forms and root/page actions are rejected. Public hostile-file intake and
broader confinement/release review remain gated.

Inspected upstream fixes include the page-tree allocation and missing-trailer
loop advisories, patched in6.21.4:
https://github.com/py-pdf/pypdf/security/advisories/GHSA-cggf-277g-3q54
https://github.com/py-pdf/pypdf/security/advisories/GHSA-5849-834g-hvw5
Extraction limitations/resource guidance:
https://pypdf.readthedocs.io/en/stable/user/extract-text.html
This scoped review does not claim zero vulnerabilities. The unchanged base image
retains the documented scanner-open, regression-verified zlib backport.

## Deployment and evidence

User explicitly approved migration13 and the existing Gather API revision update,
not a new service. Supabase function/RLS/grant checks returned six true values.
API revision `gather-library-pilot-00002-f55`, Mumbai, image
`sha256:72ce93fda395473d17dbce81247ced97f138e334ff8fef3c949cfb2ec479db8d`.
Only `GATHER_PDF_PILOT=1` and the image changed. CPU1/512MiB, min0/max1,
identities, secrets, inference service and the aggregate INR500 allowance remain.
The server advertises PDF capability; older/unupgraded servers keep PDF selection
disabled in the new client. No GitHub push is authorized.

Local evidence: 82 affected backend checks (one receipt test required its private
tmpfs output directory), six SQL acceptance groups, real Linux limited-parser
checks and a 512 MiB pinned-tokenizer+PDF composition check. These used synthetic
identities/vectors, never model inference. Frontend64 checks, lint, typecheck/build
and native rebuild passed. Live PDF acceptance is recorded separately below;
do not infer it from these fixtures. Safe receipts/screenshots: output/pdf-pilot/.

The generated live fixture is output/pdf-pilot/hosted-pilot.pdf,1090 bytes and two
pages. Its test is approved only in pilot B, with at most two real model requests.
Pilot A's retained ready and older unfinished sources must remain untouched.

Live acceptance passed on the development Windows machine: pilot B saved the
generated PDF into the same Library. Its first automatic attempt returned queued after a model readiness
HTTP429/cold start; no embedding POST was logged for that attempt. A separate
operator readiness probe then passed without inference or capacity changes.
Resume the existing exact job only; do not duplicate the import or silently
increase deadlines. Review also found that status refresh updated the status strip
but left the card's initial attempt stale. The client now synchronizes matching
nonpublished job/attempt/error metadata from the same owned status response, with
no extra reads or inference. Publication still reloads authoritative listing
metadata. A focused regression checks the observed recovery attempt and isolation
from another job. After an explicit recovery, the existing job reached ready.
The reader showed Page1's fourteen-day backup rule and Page2's archive statement.
One query, "Where do archive requests belong?", returned extracted characters0–81,
citing Pages1,2 because the one passage spans both. Opening that result displayed
the same two saved pages. Cloud HTTP logs confirm exactly two successful /embed
requests: document at12:54:19UTC and query at12:55:46UTC on31 October2026. No model
request was replayed automatically. The PDF remains in B's library; no deletion
was requested. A's sources and all unrelated services remain untouched.

Safe evidence: output/pdf-pilot/receipt.json, native-search.png, native-reader.png
and native-search-open.png. This selected real-model flow is separate from the
synthetic storage/security checks and does not establish broad retrieval quality.
The flow used native SHA4B9893A6F5E2A37E10E9A48104E4C6C9D45F8EAD12A9AF8E44C470A354A4AFC0;
the subsequent status-sync fix is covered by the64 frontend checks and rebuild.

## Remaining limits

No claim of PDF layout fidelity, arbitrary encodings, OCR, large-document quality,
clean Windows installation or public release. No silent byte/token/quota increase.
Installer verification is tracked in WINDOWS_INSTALL_QA.md.
