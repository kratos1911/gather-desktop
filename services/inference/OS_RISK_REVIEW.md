# OS finding review — 17 October 2026

## Current zlib resolution, 18 October

The stale-input-state defect is fixed and regression-verified in zlib-candidate
using a local +gather1 backport. This supersedes the earlier wait-for-vendor-only
approach below; those entries remain historical. See [backport review](zlib/README.md).
Not an official Debian update and not blanket image approval. Original installed
library fails the targeted check; patched image passes. Other findings remain. Final scan still lists 28 findings including the local
zlib package; see tests/inference/results/zlib-scan-20261018.json. No suppression.
Do not interpret scanner version matching as the behavior test or suppress it.

Scope: serving runtime manifest
`sha256:dc666a4893f77cce955c1b62f8e6b5b5a12ce8da21799f2c5db8ae252cfbf6f4`.
This review does not suppress findings, accept risk or approve deployment. The
existing 28-finding scan remains unchanged; no image/library was modified.

## zlib: upstream fix exists; Debian remediation unresolved

The [Debian tracker](https://security-tracker.debian.org/tracker/CVE-2026-85091)
still marks trixie's `1:1.3.dfsg+really1.3.1-1` vulnerable/unfixed. Its description
names later 1.3.1.2–1.3.2 non-blocking gzip writer behavior. These conflicting
signals must not be resolved by comparing version strings alone.

Upstream has a [fix commit](https://github.com/madler/zlib/commit/df84af25dc1942490e1d1c899a07619152a46148).
The [maintainer discussion](https://github.com/madler/zlib/issues/1310) confirms
the fix, advises against indiscriminate cherry-picking, and contains an unresolved
question about earlier affected versions. Community comments are not accepted
vendor adjudication for our binary. Our earlier wording "no fix" meant no
scanner-listed package fix; it did not establish absence of an upstream patch.

Decision: retain the high finding. Preferred remediation is a vendor-supported
Debian fixed package with a pinned version and verified artifact. Alternatively,
require authoritative affected-range clarification plus installed source/binary
verification. Neither condition is established here. Do not remove zlib blindly:
Python and native dependencies may need it. A custom backport or base-image switch
would require its own compatibility, provenance and security review.

## tar: disputed advisory, extraction boundary matters

The [Debian tracker](https://security-tracker.debian.org/tracker/CVE-2025-45582)
describes consecutive extraction of crafted archives into the same location and
records upstream dispute. Its GNU mailing-list link and the GNU manual could not
be retrieved in this session; no direct inspection of those pages is claimed.

Decision: retain the scanner finding with disputed status noted. Inference's
reviewed application code does not call tar or accept archive uploads. This limits
the identified application exposure; it does not prove whole-image unreachability.
Do not force-remove an essential OS package just to lower a scanner count. If
archive extraction is introduced, isolate each extraction, validate paths/links
and separately review that pipeline before enabling it.

## Verified boundary and limits

`asgi.py` accepts only bounded application/json with identity/no content encoding;
it validates the exact role/text contract before inference. `qwen.py` reads an
operator-supplied local snapshot with remote code disabled and safetensors required.
Those are application-level observations, not a complete native call-graph audit.
Rejecting compressed HTTP input does not establish that a gzip writer vulnerability
is fixed or unreachable through every dependency.

Added a focused regression covering gzip/deflate labels, tar/zip media types and
archive-like bytes disguised as JSON. All five are rejected without invoking
inference; a subsequent valid request succeeds. One synthetic loopback test passed
in the existing D: Windows environment, and the frontend build passed. No model
was loaded. Prior eight Linux tests remain valid historical evidence; the new
regression has not run in Linux because Docker's engine pipe is absent. No restart
or repeated preflight attempted. Start Docker normally to enable that later check.

## 18 October evidence update

The historical Docker/test blockers above are superseded: real local Qwen HTTP
and the startup candidate's 51 synthetic Linux checks passed. Their retained
reports are linked in docs/CLOUD_PILOT_PLAN.md and TASKS.md. No new image scan was
run for this documentation review. OS findings remain open; current pilot gates
and licence inventory are in docs/CLOUD_PILOT_PLAN.md.

## Historical next work (17 October)

Release remains blocked by unresolved OS adjudication/remediation, actual cloud
authorization and real-model HTTP/Linux shutdown evidence. Independent development
can continue with receiving service-token verification; do not wait idly for an
upstream package, or repeatedly rescan an unchanged image. Revisit these findings
when a vendor fix/classification or the image/input paths change.

## Follow-up: Debian issue checked on 18 October

[Debian bug 1146895](https://bugs.debian.org/1146895) still lists the installed
trixie version among affected versions and is tagged fixed-upstream, not fixed
in Debian. Contributor claims about unaffected older code do not constitute
maintainer adjudication. No supported fixed package was established; retained
finding, with no new scan or runtime changes. Continue independent attribution
and packaging work; re-evaluate remediation when supported evidence changes.
