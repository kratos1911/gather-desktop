# Private TXT/Markdown file pilot

26 October 2026. Scope chosen by the agent after the user delegated the choice:
private operator testing with the two existing Auth accounts. This is not a
general upload release. Local checks pass; one selected synthetic Markdown file
now has hosted save/publication/search/open evidence. It remains stored; this
file's deletion/physical cleanup have not been exercised.

## Hosted selected-file evidence

The operator saved `gather-private-pilot-example.md`, then explicitly ran the
displayed exact-job worker with TextFiles enabled. Safe receipt on disk confirms:

- Job `1dab95e4-da52-4823-9891-e60b49d3a569`: ready.
- Source `e170c166-02e6-4733-9deb-30b83104c206` (UI acknowledgement).
- Published version `89301662-ae6c-440f-b2eb-7e553455b798`.
- One real model request in this **worker** run. The operator output reports
  minimum zero restored; capacity was not independently rechecked here.
- Receipt: `output/operator-pilot/worker-1dab95e4-da52-4823-9891-e60b49d3a569-6625b0032c1a47ba8e64187a26c215ae.json`.

User screenshot then confirms the custom search returned the saved Markdown
file with citation characters 0–168, and Open displayed its saved text containing
"The Cedar team reserves two document slots for private testing." Literal HTML
markup stayed plain text. Screenshot copied unchanged to
`output/private-text-files/hosted-search-open-1dab95e4-20261026.png`.

This verifies the selected-file hosted path for one synthetic 170-byte source,
not broad semantic quality, scale, arbitrary formats or a general-user release.
Search inference-call count was not independently measured. No additional model
or worker invocation was made while recording this evidence. Do not rerun this
ready job. The separate retained older unfinished job remains untouched.

## Flow

Sign in -> select one file -> bounded local UTF-8/plain-text preview -> review
cloud disclosure and confirm -> explicit Save -> existing authenticated admission
and queued job -> separate exact-job worker -> existing atomic publication ->
custom search -> exact published text -> deletion and operator cleanup.

Selection/preview and saving do not invoke inference or launch a worker. Saving
is not indexing success. No automatic retry, warm-capacity setting or deployment
is introduced. Keep original files; the native packaged app remains sample-only.

## Operator opt-in and bounds

Default server/worker behavior remains fixed-synthetic only. A UI flag/checkbox
cannot enable file admission; the trusted operator must explicitly start:

```powershell
.\scripts\library.ps1 -Action server -TextFiles
.\scripts\library.ps1 -Action frontend -TextFiles
```

Open http://localhost:1420/ -> Operator pilot. Each side needs its switch;
server opt-in is authoritative. One selected TXT/MD/Markdown file, 1..65536
actual bytes, valid UTF-8, nonblank, no prohibited control characters. Browser
MIME/accept hints are not authorization or proof of type. Preview renders text,
never Markdown HTML. BOM, CRLF, original bytes and source-offset contracts remain
unchanged. Filenames are bounded basenames and become the disclosed stored title.

After Auth verification, server preflight reuses the parser and pinned tokenizer
and chunker. Reject more than three passages before admission; this preserves
the existing operator provider's three-inference-call process budget. No model
weights or inference are needed for counting. The application core's 16-request,
512-token passage, retry, storage, concurrency and deadline limits are unchanged.
No truncation to make a file fit. A 64 KiB valid local file may still exceed the
pilot's token budget; shorten it when the server rejects it.

Request `/v1/import` has an optional strict boolean `confirm_cloud_storage`.
Selected-file imports require true and trusted server opt-in. Confirmation stays
in the immutable retry payload; it does not grant ownership, enable a feature or
establish legal compliance. SQL still derives and enforces ownership. The generic
LibrarySession rejects this extension unless the trusted operator subclass
explicitly implements it. Two pilot UUIDs, loopback Host/Origin and exact-job
worker guards remain enforced. Arbitrary valid queries are enabled only in this
same private operator mode, under existing query/model limits.

Worker command, only after an actual acknowledged import and explicit decision:

```powershell
.\scripts\library.ps1 -Action worker -JobId <acknowledged-job-id> -TextFiles
```

This command can spend model requests/warm capacity within the existing pilot
budget. It was not run for this milestone. Do not substitute the retained old job
or reset its attempts. Source quotas remain two per account; no quota increase.

## Data handling and relevant audit gates

Consulted PRIVACY_RELEASE_AUDIT.md before adding file selection. For this restricted
pilot, relevant implementation gates are addressed by:

- An explicit trusted local mode, same two existing accounts, no signup/public
  bind/sharing or new account collection. User chose operator scope by delegation.
- Per-file review and acknowledgement before Save, disclosing full original text
  and filename storage in the existing private Supabase database in Sydney.
- Separate explicit worker/search disclosure: text goes to the private Cloud Run
  CPU service in Mumbai. There is no R2 upload in this slice.
- No client credential/file persistence, telemetry, automatic send or HTML
  execution. Application logs use fixed codes, not content/filename/token values.
- Honest retention: disconnect does not remove cloud data; no automatic expiry.
  Tombstones hide immediately, final physical removal requires operator cleanup
  of originals/derivatives/jobs. No cleanup-time promise or public SLA.
- Development privacy/terms/copyright screens now describe the actual pilot;
  production sample-only notices remain unchanged.

Public-release gates remain open: operator/contact/audience/region decisions,
processor logging/retention verification, final deletion/support policy, copyright
report handling and other applicable release requirements. Sensitive or third-party
personal content is prohibited in this pilot. This is an engineering scope/control
record, not legal advice, certification or a substitute for public release review.

## Failure and session behavior

File changes/unmount cancel local reads and reset confirmation. No auto upload.
Prepared requests preserve exact bytes and one ID across uncertain retries.
A definite first pre-admission HTTP refusal can clear the pending import so it
can be corrected. After any earlier ambiguous send, even a later definite refusal
must retain the old ID: the earlier request might already have committed.
Logout still clears local state; use restored library metadata to inspect saved
sources before deciding to create a new request after reconnecting.

## Verification

37 focused Python checks: opt-in/confirmation, Auth before tokenizer/admission,
binary/encoding/type/size/token budget, foreign owner/wrong worker job, and actual
loopback HTTP import -> synthetic worker -> search/open/delete with novel Markdown.
Repositories/embeddings are synthetic; this is not hosted SQL/JWT or semantic proof.

43 frontend checks: local file reading, actual bytes/BOM/CRLF, size/UTF-8/control/
empty rejection, plain rendering, cancellation, confirmation reset, reviewed
payload/queued state, default restrictions and immutable uncertain retries.
Build/lint pass. Production JS SHA-256 remains
`3d151cc68acc485aeb882e6761e6949131f05a49a18a6c1b975895f942c5bbb8`;
CSS and HTML asset references are unchanged. Reuse the existing native executable.

A legacy refusal test needed valid required fields after moving its guard behind
Auth; inputs were corrected without removing the refusal assertion. Control-byte
validation now uses code-point checks rather than a lint-prohibited regex.
One frontend rerun failed before collecting suites because temporary compiled
files under C: were missing. desktop.ps1 now sets TEMP/TMP under ignored D:
output/desktop-build-temp for every action and restores the caller environment.
The corrected helper passes all 43 checks and environment restoration. No runtime
installation, dependency change, model load or Docker work.

Commands, separately checking each outcome:

```powershell
$env:GATHER_PYTHON = "$PWD/output/asgi-checks/venv/Scripts/python.exe"
.\scripts\python.ps1 -m unittest tests.worker.test_operator_library tests.worker.test_library_session tests.worker.test_library_api tests.worker.test_library_flow_http -q
.\scripts\desktop.ps1 test
.\scripts\desktop.ps1 build
.\scripts\desktop.ps1 lint
.\scripts\desktop.ps1 format-check
.\scripts\library.ps1 -Action check -TextFiles
```

Browser evidence: existing pilot-A sign-in and library restoration worked after
restarting only the Gather API/frontend in TextFiles mode. Selected the ignored
170-byte `output/private-text-files/gather-private-pilot-example.md` through the
real browser chooser. BOM/CRLF text and literal HTML markup were visible in the
plain preview; confirmation stayed unchecked and Save disabled. Browser error
log empty. No Save/Search/worker action was invoked. Screenshot:
`output/private-text-files/local-review-20261026.png`.

The local-only checkpoint above preceded the hosted operator run recorded at the
top of this document. General release remains gated. Selected-file deletion and
physical cleanup remain unverified for this source; do not delete it implicitly.
Broader recovery, security/quality and distribution gates remain separate work.
