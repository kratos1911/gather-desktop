# Local zlib backport

18 October 2026. The Gather candidate replaces Debian's
`1:1.3.dfsg+really1.3.1-1+b1` with local `1:1.3.dfsg+really1.3.1-1+gather1`.
This is a Gather-maintained backport, **not an official Debian security update**.

## Fix and evidence

The direct gzip write path retains a caller's input pointer after an underlying
write failure. A later operation after clearing the error can use that invalid
state. Resetting available input and restoring the internal input pointer follows
[upstream df84af25](https://github.com/madler/zlib/commit/df84af25dc1942490e1d1c899a07619152a46148),
adapted to the older function's existing return expression. No unrelated code
or ABI changes. Absence of the newer non-blocking API does not prove safety:
[Debian's investigation](https://bugs.debian.org/1146895#55) confirms the older path.

`tests/inference/zlib_error_state.c` triggers a write failure using a read-only
descriptor, checks state, and stops before unsafe access on the vulnerable control.
The exact same executable returns 42 in notices-candidate and 0 in zlib-candidate.
On the patched path, formatting after clearing the error also succeeds.
All 102 exported symbol names/types/versions match the original library (not
an exhaustive ABI proof). Source control/fix comparison, standard/static/shared/64-bit zlib tests, nine
Python compression/archive roundtrips, PyTorch tensor archive save/load, 14 focused
staging tests and frontend build passed. No model weights loaded.

Evidence: [build](../../../tests/inference/results/zlib-build-20261018.json),
[actual image library](../../../tests/inference/results/zlib-image-20261018.json).
This verifies this system library/error path, not all bundled copies of zlib in
third-party binaries or all possible compression behavior. No CVE ignore added.

## Rebuild locally

All output belongs in `output/zlib-review` on D:. Run source retrieval as
`python -m scripts.fetch_zlib_sources`. It checks pinned descriptor/archive hashes
and refuses changed existing files. Sources originate from Debian HTTPS; the
descriptor's OpenPGP signature was not independently verified. Preserve that
provenance limitation. The builder uses authenticated Debian apt indexes.

Build `Dockerfile.builder` as a separate toolchain image. The tested builder
digest and package tool versions are recorded in the evidence; apt availability
can change future toolchains. Mount the repo read-only at `/repo` and the output
directory at `/work`; run `python /repo/services/inference/zlib/build.py` offline
with 1 GiB RAM, one CPU and 128 PIDs. Supply `GATHER_PACKAGE_MAINTAINER` from the
project's existing Git name/email so local changes are not attributed to Debian.
The build script uses a fresh directory, verifies the unpatched failure, applies
the zero-fuzz patch, runs Debian's package build/tests and checks the fixed result.

Only the runtime zlib1g package is installed; compilers and development packages
stay out of the inference image. `artifact.json` pins the reviewed package and
patch hashes. A rebuild producing different bytes requires review and a deliberate
manifest update; staging must not silently rewrite the approved hashes. Preserve
the source archives and patch as the source corresponding to this local binary.

Run existing inference image staging, then build a separate candidate. The image
checks the old package version, validates the new package hash, installs through
dpkg and verifies the new version. Patch/provenance are retained under
`/usr/share/doc/zlib1g/`. Missing/changed package or patch fails staging.

## Maintenance and release boundaries

Replace this backport with a tested vendor package when available. Keep scanner
results separate from behavior evidence: scanners may still report the CVE for a
local version. Other OS findings, native licence review, cloud IAM and deployment
approval remain separate gates. No deployment, global Docker change or protected
API container modification is part of this work.

## Final scanner result

Docker Scout 1.24.0 completed with exit zero and reports 28 findings: 1 high,
1 medium and 26 low. It identifies the local +gather1 package but continues to
flag CVE-2026-85091 as unfixed. No suppression was applied. Treat this as a
scanner-open finding with attached backport/regression evidence, not a clean
scan. [Retained report summary](../../../tests/inference/results/zlib-scan-20261018.json).
Scout's temporary archive cleanup encountered a file lock; no shared process was
stopped or forced file deletion attempted. Runtime/model behavior was not changed
in response to scan classification.
