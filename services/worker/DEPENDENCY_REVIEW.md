# Extractor dependency checkpoint: 2 October 2026

TASK-019A is **partial**. Lock generation and package review finished; rebuilt
runtime, hash-rejection probe, OS scan and container smoke remain unverified.
The rebuild failed when C: filled and Docker reported a read-only filesystem /
image-store I/O errors. Do not enable extraction networking or mark the image ready.

## Frozen inputs

- Target: Linux/amd64, CPython 3.12, Debian trixie. Other architectures are not
  supported by this wheel lock; Compose explicitly selects linux/amd64.
- Base: python:3.12.14-slim-trixie at platform manifest
  `sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b`.
  Verified through Docker registry metadata; the tag's spelling is not the pin.
- Application: 96 exact wheel versions and SHA-256 digests in
  requirements-extraction.lock. Generated from the prior tested image, then
  resolved through PyPI in Linux/amd64 with source builds disabled.
- Installer: pip 26.2.1 separately hash-pinned in requirements-bootstrap.lock.
  Docker upgrades it before installing the application lock. This change is
  authored but has not run successfully in the blocked rebuild.
- requirements-extraction.txt records direct intent. It is not the build input.

Hash enforcement detects changed artifacts; it does not certify package safety.
Registry availability is still required. This pins dependency inputs, not a
promise of identical image timestamps/digests on every builder.

## License inventory

extraction-packages.json records each wheel URL/hash and declared license
expression, classifiers, full license metadata and listed license files.
All 96 wheels declare some license metadata. pip declares MIT separately.
These declarations are an inventory, not a completed transitive-license/legal
review or a complete OS SBOM. Keep installed distributions' bundled notices.
Before distributing an image, review native/bundled components and attribution
requirements; do not infer that every dependency has Crawl4AI's license.

## Vulnerability review and disposition

scripts/audit_extractor_packages.py queried PyPI's public advisory feed for all
96 application versions plus the selected bootstrap pip. No lookup failed.
Its nonzero exit is intentional: one application dependency remains affected.

| Finding | Disposition |
| --- | --- |
| Base-bundled pip 25.0.1: advisory records for archive/wheel/path handling | Added a separate hashed 26.2.1 bootstrap upgrade. Feed reports no advisories for that selected version on the review date. Build-time bootstrap still starts with base pip and installs only the reviewed hashed PyPI wheel. Successful rebuild required before calling this remediated in the image. |
| NLTK 3.10.3, GHSA-8mgp-746c-j5xp / CVE-2026-81726, high severity | Upstream lists no patched release. Current offline adapter path does not import NLTK or accept model paths. Retain as an open gate before live extraction: assess actual Crawl4AI call paths, prohibit user-controlled model paths, and verify external sandbox isolation. Do not declare it safe solely because the current runner is offline. |
| OS/native/browser binaries | Full Docker Scout scan incomplete. First export exhausted C:; retry failed with Docker image-store I/O errors. No OS vulnerability result claimed. Chromium is not installed. |

Detailed local advisory evidence is in ignored output/extractor-audit/. The
committed facts above preserve the findings without treating a transient feed as
permanent certification. Recheck before release and after dependency updates.

## Browser dependency plan

Playwright and Patchright Python packages are pinned transitively; browser
executables and system libraries are not installed or tested. TASK-019C must
select one compatible runtime, record its exact browser revision/checksums and
OS dependencies, build them into the image, then verify launch inside the
restricted sandbox. Never download browser/model binaries on a user's device.
Do not launch a browser before the existing browser-access restriction is resolved
where applicable; current work performs no browser automation.

## Reproduction and remaining checks

1. Restore adequate C: space / Docker storage health, then restart Docker.
   Do not delete or reset user Docker data as an implicit cleanup operation.
2. Build with `docker compose -f compose.extraction.yaml build --no-cache`.
3. Run `python scripts/check_extractor_container.py`; it now checks all locked
   packages and the bootstrap version as well as existing runtime restrictions.
4. Verify a deliberately changed artifact hash is rejected by pip. Generator
   validation tests are not a substitute for that installer rejection test.
5. Run a full image/OS scan, triage findings, and retain the NLTK release gate.

To refresh after a reviewed dependency change, run
`python scripts/lock_extractor.py --image <reviewed-image-id>` and inspect the
lock and inventory diff. Refresh bootstrap separately. Rebuild, compare installed
packages, run pip check, smoke tests and the advisory check. No automatic upgrades.

Sources: [pip secure installation](https://pip.pypa.io/en/stable/topics/secure-installs/),
[Docker digest pinning](https://docs.docker.com/build/building/best-practices/#pin-base-image-versions),
[NLTK advisory](https://github.com/advisories/GHSA-8mgp-746c-j5xp),
[pip 26.2.1 metadata](https://pypi.org/pypi/pip/26.2.1/json).
