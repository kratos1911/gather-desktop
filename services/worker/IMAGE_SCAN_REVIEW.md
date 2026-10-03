# Extractor image scan review

Reviewed 3 October 2026. Docker Scout SARIF contains 51 finding records: 10 high, 7 medium, 34 low; none critical. Advisory aliases may describe the same underlying issue. This is not a clean security result.

Image: sha256:48620415c301651174d236802c6ea27a266ada75c90d1273247543640ce5e513.

SARIF SHA-256: 2412c64cface73cabfed019aae91a8374686dd65e1b478f058e610934c20cba8

Scan: Docker Scout 1.24.0, local image, full package scope. Report stored in ignored output/extractor-audit/locked-image.sarif.json. Temporary export/cache redirected to D:.

## Disposition

- OpenSSL and PCRE2: scanner lists fixed Debian versions. Update through a reviewed, reproducible base/package change and rescan before enabling live networking.
- pip bundled libraries: msgpack, urllib3 and setuptools findings point to pip/_vendor/bom.cdx.json. Upgrading application urllib3 does not address an independent bundled copy. Verify installed bundled code and remove unnecessary installer tooling from the final runtime or use a reviewed fixed distribution. Build-time exposure needs separate review.
- NLTK: remains unpatched in the prior advisory review. Gather offline runner does not import it. Installed Crawl4AI uses NLTK tokenizers and a punkt downloader; this static inspection does not prove live extraction safe. Keep user-selected model paths forbidden and retain the live-execution gate.
- Other OS records: keep open for applicability/patch review; non-root, read-only, no-network operation reduces exposure but is not a blanket dismissal.

TASK-023 tracks remediation before live extraction. No automatic upgrade, policy suppression or risk acceptance.

## Complete finding inventory

| Advisory | Severity | Package(s) | Scanner fixed version |
| --- | --- | --- | --- |
| CVE-2005-2541 | LOW | pkg:deb/debian/tar@1.35%2Bdfsg-3.1?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2007-5686 | LOW | pkg:deb/debian/shadow@1%3A4.17.4-2?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2010-0928 | LOW | pkg:deb/debian/openssl@3.5.7-1~deb13u2?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2010-4756 | LOW | pkg:deb/debian/glibc@2.41-12%2Bdeb13u4?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2011-3374 | LOW | pkg:deb/debian/apt@3.0.3?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2011-4116 | LOW | pkg:deb/debian/perl@5.40.1-6%2Bdeb13u1?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2013-4392 | LOW | pkg:deb/debian/systemd@257.13-1~deb13u1?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2017-18018 | LOW | pkg:deb/debian/coreutils@9.7-3?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2018-20796 | LOW | pkg:deb/debian/glibc@2.41-12%2Bdeb13u4?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2019-1010022 | LOW | pkg:deb/debian/glibc@2.41-12%2Bdeb13u4?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2019-1010023 | LOW | pkg:deb/debian/glibc@2.41-12%2Bdeb13u4?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2019-1010024 | LOW | pkg:deb/debian/glibc@2.41-12%2Bdeb13u4?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2019-1010025 | LOW | pkg:deb/debian/glibc@2.41-12%2Bdeb13u4?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2019-9192 | LOW | pkg:deb/debian/glibc@2.41-12%2Bdeb13u4?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2021-45346 | LOW | pkg:deb/debian/sqlite3@3.46.1-7%2Bdeb13u2?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2022-0563 | LOW | pkg:deb/debian/util-linux@2.41.5-0%2Bdeb13u1?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2023-31437 | LOW | pkg:deb/debian/systemd@257.13-1~deb13u1?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2023-31438 | LOW | pkg:deb/debian/systemd@257.13-1~deb13u1?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2023-31439 | LOW | pkg:deb/debian/systemd@257.13-1~deb13u1?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2025-5278 | LOW | pkg:deb/debian/coreutils@9.7-3?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2025-70873 | LOW | pkg:deb/debian/sqlite3@3.46.1-7%2Bdeb13u2?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2026-102474 | LOW | pkg:deb/debian/dash@0.5.12-12?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2026-35191 | LOW | pkg:deb/debian/openssl@3.5.7-1~deb13u2?os_distro=trixie&os_name=debian&os_version=13 | 3.5.7-1~deb13u3 |
| CVE-2026-42772 | LOW | pkg:deb/debian/openssl@3.5.7-1~deb13u2?os_distro=trixie&os_name=debian&os_version=13 | 3.5.7-1~deb13u3 |
| CVE-2026-53910 | LOW | pkg:deb/debian/diffutils@1%3A3.10-4?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2026-54873 | LOW | pkg:deb/debian/openssl@3.5.7-1~deb13u2?os_distro=trixie&os_name=debian&os_version=13 | 3.5.7-1~deb13u3 |
| CVE-2026-54875 | LOW | pkg:deb/debian/openssl@3.5.7-1~deb13u2?os_distro=trixie&os_name=debian&os_version=13 | 3.5.7-1~deb13u3 |
| CVE-2026-56391 | LOW | pkg:deb/debian/coreutils@9.7-3?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2026-56392 | LOW | pkg:deb/debian/coreutils@9.7-3?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2026-72897 | LOW | pkg:deb/debian/openssl@3.5.7-1~deb13u2?os_distro=trixie&os_name=debian&os_version=13 | 3.5.7-1~deb13u3 |
| CVE-2026-75804 | LOW | pkg:deb/debian/openssl@3.5.7-1~deb13u2?os_distro=trixie&os_name=debian&os_version=13 | 3.5.7-1~deb13u3 |
| CVE-2026-84784 | LOW | pkg:deb/debian/openssl@3.5.7-1~deb13u2?os_distro=trixie&os_name=debian&os_version=13 | 3.5.7-1~deb13u3 |
| CVE-2026-54872 | LOW | pkg:deb/debian/openssl@3.5.7-1~deb13u2?os_distro=trixie&os_name=debian&os_version=13 | 3.5.7-1~deb13u3 |
| CVE-2026-77696 | LOW | pkg:deb/debian/openssl@3.5.7-1~deb13u2?os_distro=trixie&os_name=debian&os_version=13 | 3.5.7-1~deb13u3 |
| CVE-2025-45582 | MEDIUM | pkg:deb/debian/tar@1.35%2Bdfsg-3.1?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2026-35189 | MEDIUM | pkg:deb/debian/openssl@3.5.7-1~deb13u2?os_distro=trixie&os_name=debian&os_version=13 | 3.5.7-1~deb13u3 |
| CVE-2026-75805 | MEDIUM | pkg:deb/debian/openssl@3.5.7-1~deb13u2?os_distro=trixie&os_name=debian&os_version=13 | 3.5.7-1~deb13u3 |
| CVE-2026-75806 | MEDIUM | pkg:deb/debian/openssl@3.5.7-1~deb13u2?os_distro=trixie&os_name=debian&os_version=13 | 3.5.7-1~deb13u3 |
| CVE-2026-102473 | MEDIUM | pkg:deb/debian/dash@0.5.12-12?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2026-59890 | MEDIUM | pkg:pypi/setuptools@70.3.0 | 83.0.0 |
| CVE-2026-97688 | MEDIUM | pkg:pypi/urllib3@2.7.0 | 2.8.0 |
| CVE-2026-102010 | HIGH | pkg:deb/debian/gcc-14@14.2.0-19?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2026-57585 | HIGH | pkg:pypi/msgpack@1.1.2 | 1.2.1 |
| GHSA-6v7p-g79w-8964 | HIGH | pkg:pypi/msgpack@1.1.2 | 1.2.1 |
| CVE-2026-103111 | HIGH | pkg:deb/debian/pcre2@10.46-1~deb13u2?os_distro=trixie&os_name=debian&os_version=13 | 10.46-1~deb13u3 |
| CVE-2026-97687 | HIGH | pkg:pypi/urllib3@2.7.0 | 2.8.0 |
| CVE-2025-47273 | HIGH | pkg:pypi/setuptools@70.3.0 | 78.1.1 |
| CVE-2026-84782 | HIGH | pkg:deb/debian/openssl@3.5.7-1~deb13u2?os_distro=trixie&os_name=debian&os_version=13 | 3.5.7-1~deb13u3 |
| CVE-2026-81726 | HIGH | pkg:pypi/nltk@3.10.3 | not fixed |
| CVE-2026-85091 | HIGH | pkg:deb/debian/zlib@1%3A1.3.dfsg%2Breally1.3.1-1?os_distro=trixie&os_name=debian&os_version=13 | not fixed |
| CVE-2026-97689 | HIGH | pkg:pypi/urllib3@2.7.0 | 2.8.0 |
