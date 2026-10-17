# Inference image security review

Follow-up interpretation: OS_RISK_REVIEW.md distinguishes scanner-listed fixes
from upstream patches, records zlib version uncertainty and tar's disputed status.
All original findings remain; this review is not remediation or deployment approval.

## Linux serving candidate — 17 October 2026

See SERVING_IMAGE.md for exact runtime/index IDs and raw report checksum. The
combined ASGI/CPU image reports 28 findings (1 high, 1 medium, 26 low), none for
Python packages. High zlib CVE-2026-85091 and medium tar CVE-2025-45582 remain
without scanner-listed fixes. Findings are retained, not accepted or suppressed.
The candidate is not deployment-approved. Compact records:
../../tests/inference/results/serving-image-scan-20261017.json.

## Patched candidate scan — 14 October 2026

Image `sha256:5d84bdf24729cacb20389734baee56fd49293eeb1bd2053d5eac1d0259c04f95`
updates Torch to 2.14.1+cpu, Transformers to 5.19.0 and the four pinned Debian
OpenSSL/PCRE2 packages. Scout 1.24.0 indexed 172 packages: **28 records, 1 high,
1 medium, 26 low**, versus 56/12 high before. No Python-package findings remain.
High zlib CVE-2026-85091 and medium tar CVE-2025-45582 have no fix listed and stay
open. No findings suppressed; the image is not deployment-approved.

Raw report: output/inference-audit/patched-20261014.sarif.json (ignored). SHA-256:
`9129cb66cdf7a36f87c81d63e93aad059d5a963db859902abebce6b07281b0fe`.
Reviewed inventory: ../../tests/inference/results/patched-image-scan-20261014.json.
Report completed despite a locked temporary-archive cleanup warning. See UPGRADE.md
for implemented changes and pending real-model compatibility checks.

## Original image scan (historical)

14 October 2026. Status: **open findings; not approved for deployment**.

Docker Scout 1.24.0 indexed 163 packages in image
`sha256:b04ad84cd1474204823070015a7f87537243714cffcb5c044789824b80b54f50`.
It reports 56 advisory records: 12 high, 7 medium, 37 low, across 16 vulnerable
packages. No records were suppressed. This is a package/feed scan, not a proof
of exploitability or a penetration test. No dependencies were upgraded this turn.

Reviewed inventory: `../../tests/inference/results/image-scan-20261014.json`.
Raw SARIF: ignored `output/inference-audit/image-20261014.sarif.json`.
SHA-256: `45118a3797c8b24c371913b97188b6b7677851b7b081614d1c17c2be17a89bdd`.
Cache/temp/report stayed on D:. Scout completed successfully but warned that a
temporary image archive was locked during cleanup. No cache deletion, engine
restart or changes to other images/containers were attempted.

## Triage and required follow-up

| Group | Evidence and action |
| --- | --- |
| OpenSSL | Installed Debian `3.5.7-1~deb13u2`; scan lists `3.5.7-1~deb13u3` fixes, including high CVE-2026-84782. Patch exact OS packages in a new image and rescan. |
| PCRE2 | Installed `10.46-1~deb13u2`; scan lists `10.46-1~deb13u3` for high CVE-2026-103111. Patch and rescan. |
| Torch | 2.8.0+cpu has multiple findings; scan lists fixes through 2.10.0. Select a maintained CPU-only release after compatibility review, regenerate Linux hashes, and rerun model/retrieval checks. Do not assume 2.10.0 clears all records. |
| Transformers | 4.57.6 has high records with listed fixes through 5.10.0 and others with no fix listed. This crosses a major version, requiring adapter/tokenizer/vector regression checks before adopting it. |
| Unfixed/remaining records | Keep open, review upstream scope and distro backports; do not silently suppress based on package presence or absence of an obvious call site. |

The [PyTorch maintainer advisory](https://github.com/pytorch/pytorch/security/advisories/GHSA-63cw-57p8-fm3p)
confirms CVE-2026-24747 concerns malicious checkpoint loading through the
weights-only unpickler and lists 2.10.0 as patched. Our configured loader uses
hash-verified local safetensors, not user-supplied checkpoints. That reduces the
identified exposure but is not a package fix or proof that every dependency path
is unreachable. No hostile checkpoint was loaded during this review.

The [Transformers upstream fix](https://github.com/huggingface/transformers/commit/a7f8e7ff37d87d1a1a0c8cf607971c607741452f)
is relevant to config-driven kernel loading. The current runtime uses a pinned
operator-controlled Qwen config, explicit SDPA, local-only loading and no network.
Do not rely on `trust_remote_code=False` alone as a complete mitigation.

Other reported paths include tokenizer saving, custom generation, X-CLIP
conversion, LightGlue initialization and Torch operations not explicitly invoked
by our adapter. Their apparent absence is a code-review observation, not a
formal non-exploitability determination. OS libraries can remain transitively
reachable. Network isolation/read-only/non-root/resource limits reduce impact;
they do not clear findings.

Before public/API deployment: patch OS packages, upgrade/test the AI stack,
rescan the resulting image, review remaining applicability and dependency
licences, and retain evidence. Keep this scanned image for comparison; benchmark
numbers apply to this exact image and must be remeasured after upgrades.
