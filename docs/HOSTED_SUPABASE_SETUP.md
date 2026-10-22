# Hosted Supabase operator setup

Current checkpoint: operator saved DPAPI credentials. Agent verified decryption
under the owning Windows user and both actual restricted hosted logins over TLS.
Read-only check_hosted_database.py performs only connection policy/current-role
reads and rolls back. Initial combined probe passed admission but failed worker;
no detailed initial cause was retained. A single focused diagnostic with safe
codes and unchanged five-second deadline passed worker. Do not characterize this
as a proven authentication/configuration defect. No document or job writes.
The formerly blocked frontend build now passes; approval review became available.
14 focused checks pass (password setup, credential store, read-only probe).

Next blocked input: no saved public project API configuration; CLI key lookup
could not access this Gather project under its current login. No Supabase connector
is available. Hosted Auth test users and a real-session import/search flow remain
unverified. Operator should retrieve the publishable key from Project Settings ->
API Keys and inspect Authentication -> Users. No secret/service key is needed in
chat. Earlier build/credential-pending statements below are historical.

Latest: user reports password setup success=true, passwords_committed=true and
both restricted logins verified. That is user-run hosted TLS/login evidence.
Chat-exposed pilot passwords remain in use by explicit user choice; rotation is
pending, not completed. Do not copy them from conversation into source or tools.

Local encrypted loading is now prepared: run
`./scripts/python.ps1 -m scripts.store_supabase_credentials --save` in an interactive
PowerShell window. Enter only the two existing backend passwords (each twice),
not the postgres password. This stores current-user Windows DPAPI ciphertext in
ignored output/credentials on D:, after checking encryption/decryption in memory.
No network/database write occurs. Existing files are never silently replaced.
`--check` verifies decryption/schema locally; it is not database authentication.
The backend calls local_credentials.database_config(role), which loads the fixed
Sydney host/project/CA and hides the password in its configuration repr.

This is operator tooling, never a distributed desktop credential bundle. A process
running as the same Windows user can decrypt; moving it to another computer/account
is not a supported deployment method. Cloud runtimes require server secret storage
later. Python plaintext memory is not guaranteed to be fully erased. DPAPI has no
machine-wide flag or UI fallback. Twelve focused tests and a real in-memory DPAPI
roundtrip with synthetic bytes pass. No personal credentials have been stored by
the agent. Frontend build remains pending after the earlier approval-review usage
limit; these changes remain uncommitted.

Reference: https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata

Follow-up: user reported the generic setup-stopped message after all prompts.
Exact cause/commit state was not established. Added role-specific local validation
errors and --check-input, which never starts a database child. Eight checks pass,
including short-password rejection before network and input-only mode. Ask the
operator to run that mode before another --apply. Build remains pending as below.

22 October 2026. User chose to keep Sydney for the pilot.
Project: fatolholcjxpwocnpzws. Session pooler:
aws-0-ap-southeast-2.pooler.supabase.com:5432.

User reports all seven repository migrations applied in order and the shown
RLS/schema/table/function checks match expectations. This was manual SQL Editor
execution, not CLI migration-history synchronization. Do not blindly db push.
User also reports creating gather_admission and gather_worker with LOGIN,
NOINHERIT and no elevated attributes, granted only their respective existing
coordinator/worker roles. No passwords set or live backend login verified yet.

CA file inspected: output/supabase-cli/prod-ca-2021.crt, Supabase Root 2021 CA,
valid through 26 April 2031; no private key. Actual TLS handshake remains pending.

## Password command

Save two distinct passwords of at least 24 characters in a password manager.
From the repository PowerShell prompt:

```powershell
.\scripts\python.ps1 scripts/set_supabase_passwords.py --apply
```

The existing DATABASE administrator password is prompted first (not GitHub or
Supabase website sign-in), then each new password with confirmation. Input is
hidden and never saved by the helper. It refuses echoed-input fallback. The
operator enters credentials directly; never send them to chat.

The helper pins this project/host/CA, verifies TLS, checks role attributes and
exact memberships before altering either password, generates SCRAM verifiers
through libpq, updates both in a transaction, then tests both restricted logins.
No admin password, role attributes, grants or user documents are changed.
Credentials reach a bounded child through stdin only; no credential arguments or
inherited PG environment. Network work has a 30-second operator-setup deadline,
five-second connect/statement limits and no automatic retry. This does not change
the application's five-second database-operation deadline.

Expected success: success=true, passwords_committed=true, both logins listed.
If passwords_committed=true but success=false, passwords changed but login checks
failed. null means uncertain commit outcome; do not rerun blindly. Share only the
safe JSON result. Raw errors, passwords and SCRAM verifiers are not printed.

Six mocked/local checks and preview pass; live setup has NOT run. The required
frontend build was rejected because automatic approval review hit a usage limit;
the build did not execute. No bypass attempted. Changes remain uncommitted pending
that check. Existing unrelated root logs remain untouched.
