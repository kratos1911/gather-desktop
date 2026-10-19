# Bounded inference cloud pilot

19 October update: [guarded cloud startup](CLOUD_STARTUP.md) is implemented and
host-tested. Linux image verification is pending Docker availability. Earlier
rows below retain their dated evidence; no cloud deployment has occurred.

18 October 2026. Reviewable proposal, **not approved or deployed**. Scope is one
private inference service using fictional test text. This is not desktop rollout.

## Configuration proposal

| Setting | Proposed value |
| --- | --- |
| CPU / memory | 2 vCPU / 5 GiB; retain measured local budget |
| Processes / concurrency | One server, one model child, one request per instance |
| Autoscaling | Minimum 0, service maximum 1; not a hard cost cap |
| CPU allocation | Instance-based billing, subject to explicit spend approval |
| Time limits | Existing 15 s client and compute limits; proposed 30 s platform timeout; existing 90 s model startup bound |
| Model | Qwen3-Embedding-0.6B, revision `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`, existing 512-dimensional contract |
| Artifact | Private immutable digest, verified offline weights and retained notices; release image not yet assembled |
| Authentication | Invoker checking enabled; only approved caller service accounts; independent application token verification |
| Project / region / spend | Unselected for this pilot; obtain explicit decisions before provisioning |

**CPU correction:** managed_auth.py refreshes trusted keys on a background thread.
Request-based CPU allocation does not guarantee that thread runs while idle.
Instance-based allocation supports it while an instance lives, but bills idle
lifetime too. Minimum zero still allows shutdown. Fresh keys remain required;
never extend their lifetime to mask scheduling failures. This supersedes the old
request-based proposal, not an applied billing setting. Source:
[Google billing and CPU allocation](https://docs.cloud.google.com/run/docs/configuring/billing-settings).

## Evidence and release gates

| Item | Evidence / remaining work |
| --- | --- |
| Local model | Real loopback HTTP passed: startup 12.68 s, peak 3.98 GiB; cloud cold start remains unmeasured |
| Packaging | startup-candidate passed 51 synthetic Linux checks; it lacks bundled weights and remains loopback-only |
| Public keys | Live Google certificate fetch passed; it does not establish real caller token, IAM or proxy-header behavior |
| OS security | Retain 17 October scan: 28 OS findings (1 high, 1 medium, 26 low); unchanged base/dependency layer evidence reused, no new scan |
| Model licence | Pinned model card declares Apache-2.0; retain licence, attribution and applicable upstream notices in the release artifact |
| Dependencies | All 47 cached serving wheels match lock hashes. Inventory records metadata and notice-file paths; tokenizers upstream licence files now retained with provenance and included by staging. Notice image built and verified; pinned model attribution included. Full native attribution review remains pending |
| Native components | Wheel metadata alone does not audit bundled native code or Debian licences. Complete distribution notice review remains open |
| Cloud operation | Explicit guarded cloud entry point, immutable release image, intended IAM policy and measured pilot still needed |

Inventory: [licence evidence](../tests/inference/results/license-inventory-20261018.json).
Model declaration: [pinned model card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/blob/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3/README.md).
Security: [retained OS review](../services/inference/OS_RISK_REVIEW.md).
The system zlib error-state defect now has a [verified local backport](../services/inference/zlib/README.md); it is not an official Debian update. Other security gates remain.
The [Debian zlib tracker](https://security-tracker.debian.org/tracker/CVE-2026-85091)
still does not establish a supported fixed package for our image. Do not suppress
the finding from version-string inference. The local backport is the implemented remediation for this path; vendor replacement
and other OS findings remain tracked. No blanket risk exception is granted here.

## Ordered next steps

1. **Release prerequisites:** notice collection and model attribution are packaged
   and verified. Complete native dependency attribution and document exact OS
   remediation/adjudication evidence. These do not block local cloud-mode coding.
   No model run is needed for this work. Do not repeatedly scan unchanged layers.
2. **Local cloud packaging:** implement explicit cloud mode without changing the
   safe loopback default. Require validated audience/caller pairs and port, use
   verified immutable weights, retain shutdown/busy/deadline controls. Test with
   synthetic engines first. Build the release image only after its input gates
   pass; scan changed layers and perform the necessary real-image smoke once.
3. **Approved pilot:** present exact project, region, caller IDs, image digest,
   IAM changes, billing choice, cost estimate and teardown scope for approval.
   Only then provision and run the acceptance sequence below.

## Pilot acceptance sequence

- Record configuration and digest, with no tokens or document text in logs.
- Anonymous, wrong caller and wrong audience requests must fail. A permitted
  caller must succeed through both platform and application verification, using
  the existing dual-header client. Confirm actual permissions, not just config.
- Run one cold and five warm fictional-text requests sequentially; record startup,
  latency, RAM, status, dimensions and model identity. This small sample is not
  a throughput or p95 claim. Stop on auth bypass, identity mismatch or resource breach.
- Exercise one concurrent pair: bounded rejection, no extra model child. Verify
  cancellation separately; a platform timeout alone does not stop computation.
- Test an idle period longer than the key freshness cap. Confirm refreshed keys
  if the instance survives, or clean startup if it scales down. Simulate key
  endpoint failure locally; do not alter shared Google networking to test it.
- Cold-start failure within the 15 s client budget remains a release blocker.
  Choose explicit warm-up or separately approved capacity; do not silently retry
  or increase the budget. Readiness does not eliminate cold-start waiting.
- Stop the harness after the sequence. Review measured usage and billing lag.
  Request-count bounds and max instances are not financial guarantees.

Before running, approve teardown of only the new pilot resources. On failure,
stop test traffic and revoke the pilot's invoker grants to prevent new authorized
calls; in-flight work can persist until cancellation/deadline. Delete the owned
pilot service as authorized, verify removal, and separately account for retained
registry images/logs. Never use maximum-instances zero as an assumed off switch.
Do not modify shared services or protected API containers.

## What follows

After pilot acceptance: connect trusted ingestion and published search to that
endpoint, then authenticated desktop import/open/delete. Original storage,
dispatch, privacy disclosures and user quotas remain separate release work.
No chat, additional formats or UI redesign is included here.
