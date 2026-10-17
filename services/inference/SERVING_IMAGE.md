# Linux serving candidate

This packaging slice adds the ASGI dependencies and code to the existing CPU image.
It does not enable public ingress or change the default stream entry point. Trusted
application construction and receiving cloud authentication remain separate gates.
No weights or credentials are included; no production image is promoted.

## Reproduce

Use `output/inference-asgi` on D:. Populate its wheels directory with the exact
artifacts in requirements-serving.lock: reuse the 34 original locked wheels, then
download the seven added Linux CPython 3.12 wheels. Install neither into shared
environments. The inventory in tests/inference/results/serving-wheel-inventory.json
records added wheel filenames, SHA-256, licence metadata and declared dependencies.
MIT and BSD-3-Clause declarations require their notices to be retained; wheel
installation retains dist-info licence files. This inventory is not a legal audit.

```powershell
python -B -m scripts.prepare_inference_image --serving --build-dir output/inference-asgi
docker build --tag gather-inference:asgi-candidate output/inference-asgi
```

Lock regeneration requires deliberate `--update-lock`; normal staging rejects a
different wheelhouse. Serving staging additionally rejects any changed or missing
original model dependency, even during regeneration. Exact Python file allowlists
exclude stale code from reused build contexts. Model materialization is skipped.

The unchanged Dockerfile uses the existing digest-pinned Python base, pinned Debian
updates, offline hash-required wheel installation and `pip check`. It removes pip
and ensurepip, and runs as UID/GID 65532. Package-source access is needed only when
preparing wheels/OS layers. Debian repository availability still limits clean
rebuilds: this is not a fully archived, hermetic OS snapshot.

Shared dependencies keep the Linux model versions (not the Windows test versions),
including click 8.5.0 and idna 3.20. Linux tests must therefore validate the combined
environment explicitly. No source distributions or dependency upgrades are used.

## Verification boundary

17 October candidate ID:
`sha256:014831ac1460b2b75c0f458b8d26dab0595384c257b839b4795dea95b73146f7`.
Offline install and `pip check` passed for 41 distributions. Four staging tests,
eight synthetic ASGI tests in the Linux image and the frontend build passed.
The container smoke confirmed no installed pip or bundled /model directory; image
metadata confirms UID/GID 65532. No model was loaded. The Docker build's token-name
warning refers to HF_HUB_DISABLE_IMPLICIT_TOKEN=1, a protective flag, not a secret.

Review rebuild `gather-inference:asgi-context-check` excluded a harmless unapproved
marker file with tightened exact-path rules. Its index ID is
`sha256:cecf1ac45fee9301c6419f6a325efa257b4c9ff25dfd6412038639c569d88fde`;
both builds share runtime manifest
`sha256:dc666a4893f77cce955c1b62f8e6b5b5a12ce8da21799f2c5db8ae252cfbf6f4`
and config `sha256:a5e2f2085d0178bba64ba5647d1662f01f12bead02aebf7c9fc205c0af7ed737`.
Only build attestations differ; runtime tests apply to the identical runtime image.

Scout report: 28 findings (1 high, 1 medium, 26 low), no Python-package findings.
High zlib CVE-2026-85091 and medium tar CVE-2025-45582 remain listed without fixes.
No findings were suppressed. This candidate is **not deployment-approved**.
Reviewed records: tests/inference/results/serving-image-scan-20261017.json.
Raw report: output/inference-audit/asgi-20261017.sarif.json, SHA-256
`964a0645b49c63efb27f65d81946b41d50339e2eb3b5a5af94b70ab8cae139f9`.
The tool session ended before its exit status was recovered; the complete parseable
report was recovered and reviewed without repeating the scan. No scanner exit-code
success is claimed. Counts match the prior CPU scan, not proof of zero new risks.

Next: assess remediation for the OS findings against upstream fixes, then complete
the receiving cloud-auth boundary and bounded real-model HTTP/Linux shutdown checks.
Any vulnerability acceptance or deployment approval remains explicit and separate.

Run synthetic ASGI tests with network disabled, no published ports, read-only root,
bounded tmpfs, dropped capabilities, no-new-privileges, and explicit memory/CPU/PID
limits. Mount only test fixtures read-only, never models or personal documents.
Record the resulting image ID and current scan separately from historical evidence.

Cloud IAM, actual OS SIGTERM, model startup/HTTP resource measurements and unresolved
vulnerabilities remain release gates. A passing synthetic HTTP suite does not
establish semantic accuracy or permission to deploy.

The hash-required approach follows [pip secure install guidance](https://pip.pypa.io/en/stable/topics/secure-installs/).
