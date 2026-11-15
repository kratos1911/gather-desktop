# Recruiter trial model quotas

The first recruiter trial backend change adds durable model allowances to the
existing private library. The cloud build opts in with `GATHER_TRIAL_MODEL_USAGE=1`
after migration `202611150001_trial_model_usage.sql` and an operator-configured
policy. The migration seeds no limits and grants no client access. A missing
policy, unavailable database or uncertain commit prevents model inference.

Search binds a reservation to the freshly verified account. The worker binds
its reservation to the owner of the exact job under a live lease. PostgreSQL
locks one policy row and updates both counters in the same transaction, so
connections and instances share the same limits. Each account gets a UTC daily
allowance, and the service shares one UTC monthly allowance. Stored data is
limited to the current counters and period dates, with account counters removed
on auth-user deletion. The monthly service total survives account deletion.

One committed reservation permits one outbound embedding attempt. Provider
failures, cancellation after commit and uncertain commits can consume that
unit. The app never retries a reservation on an uncertain response. Cached
queries and empty-library searches avoid model reservations. The desktop
connection check displays the account allowance and distinguishes exhausted
account and service limits. The local process still admits one inference at a
time.

The counters guard embedding attempts across instances. Readiness probes and
infrastructure can incur separate charges. Set actual limits only after reviewing
trial usage and budget. Automatic processing still uses existing bounded
recovery when a reservation is denied. Before enrolling recruiters, make quota
exhaustion actionable for queued imports, verify continued processing for other
accounts and validate storage and parser limits against realistic files.

This work is verified locally. Hosted rollout, account enrollment, and representative
file acceptance remain pending. The live app still uses the existing pilot mode.
