# Verified artifact startup

18 October: local implementation verified; updated Linux image build is blocked.

The packaged model-manifest.json is a portable projection of the previously
verified qwen-download.json: model/revision, total size and ten exact file sizes/
SHA-256 hashes. It contains no host paths, weights, tokens or downloaded code.
The manifest is trusted application code reviewed with the image, not supplied by
an incoming request. Changing both the trusted manifest and weights is outside
what a file-hash check can detect; immutable image provenance remains required.

artifacts.verify_snapshot requires an absolute directory and the exact flat file
set. It rejects symlinks/reparse points, directories, missing/extra files, unsafe
names, duplicate entries, wrong identity, sizes and hashes. Manifest reads cap at
64 KiB/32 entries; total declared bytes cap at 2 GiB. Streaming hashes use 1 MiB
buffers and a cooperative 30-second check between reads (not a hard timeout for a
stalled filesystem). The model directory must remain operator-owned and immutable,
with a read-only mount throughout service life. Hashing does not defeat subsequent
privileged host writes. No remote downloads, token lookup or model load occurs.

startup.build_verified_app validates identity, verifies files, constructs the
existing Qwen Runtime, then composes the managed-auth ASGI lifespan. Keys are
obtained before model load. Existing 90-second model startup and 15-second compute
limits remain unchanged. This does not alter tokenization, vectors or model code.

Explicit local entry point (paths must be operator-provided, never request data):

```powershell
python -B -m services.inference.startup --identity <operator-policy.json> --model <absolute-readonly-model-directory> --port 8080
```

This entry point binds loopback only, with no public-host switch or credential
fallback. It will fetch Google keys on lifespan startup; the command was NOT run
against live Google in this milestone. Default Docker stream entry point remains
unchanged; select this module explicitly for future controlled integration checks.
Cloud public ingress/IAM and baked model packaging/licence approval remain gated.

## Evidence

- 13 host checks passed: five artifact checks, four startup checks, four staging
  checks. Includes corruption, missing/extra files, traversal, wrong revision,
  duplicate JSON keys, symlinks, hash deadline, deferred runtime and lifecycle.
- First sandbox invocation stopped after artifact checks during Windows asyncio
  initialization; only the exact test processes were terminated. Permissioned
  focused rerun passed; the aborted run's trailing exit status is not test evidence.
- Existing real ten-file snapshot verified in 1.357 s without loading the model.
- Required frontend build passed; no native inputs changed.
- Staged exact source allowlist plus portable manifest into output/inference-auth
  with the unchanged 47-package lock. No weights or credentials copied.
- Preflight: 5.04 GiB host RAM, 85.29 GiB D: free, 47 cached wheels. Docker Linux
  engine pipe was absent; no build retry, Docker launch/reset or API changes.

Next: open Docker Desktop until the Linux engine is running, then build a separate
startup candidate and verify the packaged modules/manifest with synthetic Linux
checks. Reuse prior model evidence where unchanged; do not claim Linux validation
of this source from the older image. No deployment or push occurred.
