# Model release and Gather pilot

Updated 21 October 2026. **Local release build and real-model verification are
complete. Cloud account access and final security/resource approval remain pending.
No upload, API enablement, IAM change or deployment has occurred.**

## Milestone 1: release image

Built `gather-inference:release-candidate` with the ten pinned Qwen model files,
existing dependency notices, native source notices and non-root cloud startup.
Current digest:
`sha256:fa60e15879e583c9bff8e04b78f774ebd7fd65eb8b9022304d249d125fb291fc`.
The source base is the previously Linux-verified cloud-startup candidate.
Only a small identity-validator overlay follows the model/notice layers.

The release preparation caught a real compatibility error: the audience validator
accepted simplified fixture hostnames but rejected Google's regional/generated
multi-label run.app hosts. The fix accepts bounded DNS labels under exactly
HTTPS run.app origins, still rejecting userinfo, ports, paths, query strings and
lookalike suffixes. JWT audience verification remains exact, not wildcard-based.
[Google service URL formats](https://docs.cloud.google.com/run/docs/triggering/https-request).

Native attribution collection used SBOMs inside hash-locked wheels, not guessed
repository versions. Collected notices for all 439 hashed crate versions, including
non-runtime targets conservatively. Three missing archive notices were recovered
from immutable commits recorded in their source archives. r-efi puts licence text
in AUTHORS. The 14 local project components are recorded separately; parent-project
notices remain in the wheel notice bundle. This is declared-component provenance
and notice retention, not legal certification or proof about undeclared binaries.

Caches/source archives stay under output/native-notices on D:. Bundle SHA-256:
`314643eab529c387be785b8841bb381499f6dc094e03507d04956ffa30d301e9`.
The release builder rejects a different base image or unreviewed/incomplete
notice bundle. It verifies model hashes before and after staging. Rebuilds reuse
unchanged staged model files and keep configuration/credentials out of the image.

Verification completed:

- 4 release packaging tests and 4 synthetic HTTP harness tests pass.
- 34 identity/verifier/cloud-startup tests pass after the hostname fix.
- Required frontend build passes.
- A separate 128 MiB, network-disabled, read-only container verifies all ten
  baked model file hashes, non-root UID, non-writable files/directory and the
  embedded native notice bundle. This did not load the model.

Evidence: release-build-20261019.json and release-integrity-20261020.json under
tests/inference/results. Existing zlib-backport regression and scanner findings
remain dated evidence; the added model/notice layers have not received a fresh scan.
The scanner still reports the locally patched zlib CVE plus other findings. No
blanket security waiver is implied.

**Real-image check passed, 21 October:** all four HTTP requests and required
rejection/recovery/cleanup checks passed on the exact baked candidate. Startup
18.551 s; requests 0.858/1.179/7.761/1.021 s; peak 4,388,347,904 bytes (4.09 GiB),
below 5 GiB. No OOM or outer timeout. Host preflight reached 4.20 GiB after the
authorized cache/app cleanup; the 4 GiB threshold was not lowered.
Evidence: tests/inference/results/qwen-release-http-20261021.json.

The host stderr reader hit a Windows locale-decoding error; valid model JSON and
container exit zero were retained. The harness now captures raw bytes and keeps
stderr logs. Two subprocess encoding tests and four synthetic HTTP tests passed;
the model was not rerun for this diagnostic-only fix. Two protected API restart
counts increased during the run; no API mutation commands were issued and no
cause is inferred. All detailed caveats remain in the evidence.

Reproduce only after relevant changes, with sufficient RAM:

```powershell
.\output\model-benchmark\venv\Scripts\python.exe -B -m scripts.check_inference_container --candidate --profile http --release
```

It retains 2 CPUs, 5 GiB with no extra swap, 15-second compute deadlines and a
300-second outer timeout. No host model mount is allowed in release mode. It
checks baked artifact hashes before loading. Results go into the separate
output/inference-results/release directory. This is real local HTTP evidence
with an ephemeral bearer, not Google IAM or a repeated retrieval benchmark.

## Milestone 2: concrete pilot plan

Use **Gather Development, gather-development-511211, Mumbai/asia-south1 only**.
The browser confirmed this project on 19 October. It displayed an unused
INR 28,797 trial balance expiring 9 January 2027; that is an observed account
display, not a promise that every charge is covered.

The previously configured CLI project is Intrixshield and is explicitly excluded.
Do not change global gcloud defaults. Every future command must specify Gather's
project and an authenticated Gather account explicitly. Current CLI credentials
only include the Intrixel work account; its project read was denied. The browser
being signed in does not sign the local CLI in.

Sign in locally with the personal account shown in the Gather console, preserving
the active work-account configuration:

```powershell
gcloud auth login --no-activate
```

Do not paste tokens or passwords into chat. After sign-in, verify access with an
explicit --account and --project before creating anything.

[pilot.json](../deploy/cloud-run/pilot.json) is the reviewable settings manifest,
not an executable deployment or authorization. Proposed resources are one private
Cloud Run inference service, one regional Artifact Registry repository, and two
dedicated service accounts. Runtime gets no Supabase/R2 access. The caller gets
run.invoker on this service only; token impersonation, if needed for local pilot
checks, is granted only on the caller account to the approved operator. No
allUsers binding, downloaded keys, GPU, VM, VPC connector or remote image build.

Before deployment, resolve the actual project number and caller numeric subject,
then generate operator identity/policy files with exact audiences. A final small
configuration layer may supply these non-secret files; it must be reviewed and
recorded by digest. Never deploy the current image with missing or invented policy
values. Confirm actual IAM, token/header handling and cold-start behavior in the
pilot; configuration validation alone does not prove them.

## Cost envelope and stop conditions

User-approved planning ceiling: **INR 500 total for one pilot**, including charges
consumed from trial credits. This is a ceiling, not a required spend or prepaid
subscription. Final resource-creation approval is still required.

Plan one supervised window of at most 60 minutes, at most 12 test requests, no
automatic retries and no unattended public access. Stop and tear down the pilot
service after testing; remove its image within 24 hours under the approved cleanup
scope. Retained registry artifacts continue accruing storage charges.

Planning arithmetic before free allowances, credits or tax:

- Mumbai is listed as Tier 1. At the published instance rates, 2 vCPU plus 5 GiB
  for one hour is `(2 * 0.000018 + 5 * 0.000002) * 3600 = USD 0.1656`.
- Allowing a conservative 6 GiB of registry storage for 24 hours gives
  `6 * 24 * 0.000136986 = USD 0.019726`. Actual storage/account usage can differ.
- Combined compute/storage illustration: about USD 0.1853. At a deliberately
  illustrative INR 100/USD budgeting conversion, about INR 18.53 before tax,
  transfer, logs and other charges. This is not a live exchange rate or invoice
  quote. Use actual INR SKUs before final approval and keep substantial headroom.

Sources: [Cloud Run pricing](https://cloud.google.com/run/pricing) and
[Artifact Registry pricing](https://cloud.google.com/artifact-registry/pricing),
reviewed 19 October. Same-region registry pulls avoid cross-region transfer;
internet responses and retained logs still need accounting. No free-tier balance
is assumed in this estimate.

Maximum instances and budget alerts are not hard spending caps. Do not promise an
absolute INR 500 cap without verifying an applicable enforced mechanism. Do not
apply account-wide shutdown controls that could affect Intrixshield. Before
approval, review project-scoped spend controls and cancellation/cleanup for only
Gather's resources. If those controls cannot support the user's ceiling, stop and
explain the limitation instead of deploying.

## Remaining handoff

1. Personal-account CLI sign-in and read-only verification of Gather.
2. Reuse the completed real-image test unless relevant inputs change.
3. Review the concrete IAM/registry/service/cleanup changes and remaining security
   findings with the user; only then request deployment approval.
