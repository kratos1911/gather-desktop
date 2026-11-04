# Private image OCR slice

4 November 2026: private PNG/JPEG English OCR is deployed and its selected native
flow passed. User prioritized this before bookmarks/MCP and approved the cloud
rollout plus 2 GiB for the existing Library API. CPU/scaling and aggregate INR500
pilot allowance remain unchanged. This is not photo object/scene retrieval.

## First outcome

Select a bounded PNG/JPEG -> explicit cloud consent -> durable processing -> OCR
text -> existing pinned Qwen text embeddings -> atomic publication -> semantic
search -> exact saved image/text-region opening -> deletion and physical cleanup.
Reuse existing ownership, lease, version, request, retry and storage contracts.
Object/scene search is a separate visual-embedding slice; OCR does not establish it.

## Current local candidate and evidence

The earlier PaddleOCR mobile shortlist remains an unmeasured alternative. The
first tested CPU candidate is Tesseract 5.5.0 LSTM with fixed English traineddata
SHA-256 7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2,
and hash-verified Pillow 13.0.0. Runtime inputs/probe image are under ignored
output/ocr-pilot/. No end-user model download or new hosted OCR service.

Two generated PNG/JPEG fixtures passed real OCR under the existing 192 MiB
address-space, 3 CPU-second and 5-second wall parser limits. The complete bounded
C-API wrapper took about 1.7–2.3 seconds per fixture in that local run. This is not
general OCR accuracy, production latency or live semantic-search evidence.
Synthetic adapter checks are separate from the later live flow below.

## Contract

- Original and extracted text limits stay 64 KiB. At most 1,048,576 decoded pixels,
  4,096 per side, one frame, 128 OCR line regions and 2,048 recognized words.
- Actual decode occurs after authentication inside the shared disposable Linux
  parser slot. Reject SVG/other formats, animation, malformed/oversized images
  and empty OCR. EXIF orientation is applied before OCR; coordinates address the
  upright image. Alpha is composited onto white. Do not silently resize/truncate.
- Use a fixed in-process Tesseract C API with one OCR thread; cancellation kills
  the parser and leaves no OCR subprocess descendants. This is not a full OS sandbox.
- Retain original SHA, text SHA, parser/engine/language/model identity, upright
  width/height, Unicode offsets, line boxes and engine confidence. Confidence is
  an engine score, not a correctness guarantee. Keep low-confidence text visible.
- Search reads metadata/text only. Explicit opening retrieves original bytes
  through an owned, exact-published-version RPC; never expose staging or a bucket.
- New image capability is trusted/default-off. Client selection cannot enable it.
  Existing two-account, three-passage/model-attempt and explicit-recovery gates stay.

Frontend wiring and 80 checks pass. Twenty isolated SQL groups pass for image,
PDF and DOCX storage. The affected backend pass had 148 checks; the final security
overlay passed 45 focused OCR/auth checks, both PNG/JPEG originals and eight
additional decode/OCR cases. Overlapping groups are not one unique total.
Frontend/typecheck/format, native/installer builds and exact installed identity pass.

## Hosted/native acceptance

Migration 16, 202611040001_image_ocr.sql, is applied to Gather/Sydney. Browser SQL
confirmed readers/schema, forced RLS, private table access and worker-only staging.
API revision gather-library-pilot-00008-t86 uses image
sha256:af36fbc5cc4fb7105630fe6c5ace1cdc9c4e2e813ef4b5ddead1443e63cc25ca,
CPU1/2GiB, min0/max1. Existing model/IAM/secrets remain unchanged.

Only the explicitly approved generated DOCX source
3c55a093-daae-4712-afa3-5217917d0bb0 was deleted and fully cleaned through the app.
Pilot B then selected/reviewed/saved synthetic-note.png (15,911 bytes). It became
ready automatically without explicit recovery; one document embedding and one
query embedding were used. “Where should I send an archive request?” returned the
image first with the Cedar-queue passage, regions 1–3 and text offsets 0–100.
Exact original opening, three recognized regions and confidence disclosure passed
in the installed Windows app. The generated image remains for inspection.
Personal PDF and pilot A sources were not modified. Search can read other owned
published sources; this is not a claim that personal content was never retrieved.

Safe evidence: output/ocr-pilot/live-acceptance.json, processing-log.json,
deployment.json and native-image-reader.png. This cold dispatch took 44.99s,
including 0.77s parsing and overlapped startup. One sample is not a latency or
accuracy guarantee. Signed-out controls and the GUI subsystem remain intact.
The browser fallback was rejected by the native-only origin boundary as intended;
it was not widened. The direct Windows control skill completed live acceptance.

References: [Tesseract C API](https://github.com/tesseract-ocr/tesseract/blob/5.5.0/include/tesseract/capi.h),
[TSV/engine documentation](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html),
[PaddleOCR published measurements](https://www.paddleocr.ai/main/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5.html).

## Package review

The completed candidate scan reported 106 findings (9 high/7 medium/90 low), not
a clean image. The final runtime removes 32 unused OS packages including system
expat, CLI/font/GUI dependencies; inventory comparison shows no added or changed
remaining OS package versions. Hash-verified pyasn1 0.6.5 addresses four high
decoder advisories; setuptools 84.1.0 addresses the available patch. Forty-five
focused OCR/auth checks and ten real generated-image cases pass on this runtime.
The repeat full scan was stopped during indexing because of excessive host RAM
use; reuse of its predecessor scan plus exact inventory/patch evidence is not a
new full-image scan or final vulnerability count. Raw reports stay under output/ocr-pilot/.

libxml2 CVE-2026-86140 and CVE-2026-74860 remain unpatched scanner findings.
Gather's OCR path passes decoded RGB pixels, not XML, to Tesseract; Python libxml2
bindings are absent, and DOCX rejects DTD/entities in its bounded stdlib parser.
This applicability reasoning is not proof of absence of all native-code risk.
The existing zlib backport remains flagged and unsuppressed; its provenance and
earlier payload evidence remain applicable. Keep public hostile uploads gated.
Sources: [pyasn1 patch release](https://github.com/pyasn1/pyasn1/releases/tag/v0.6.5),
[Debian libxml2 tracking](https://security-tracker.debian.org/tracker/CVE-2026-86140),
[binding advisory](https://security-tracker.debian.org/tracker/CVE-2026-74860).
