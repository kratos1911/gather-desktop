# Gather

A Windows knowledge-library project for finding saved material by meaning.

The private Windows pilot uses hosted Auth, automatic TXT/Markdown processing,
semantic search and exact saved-text opening. Owner-scoped deletion/cleanup is
verified through the app. Default builds retain a separate sample preview.
General signup, production distribution, other formats and chat are not released.

## Start here

- [Current state and constraints](docs/MEMORY.md)
- [Current tasks and acceptance criteria](TASKS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Topic index / Obsidian hub](docs/PROJECT_HUB.md)
- [Working rules](AGENTS.md) and [workflow](RULES.md)

Read current context once, then only the contract relevant to the task.
[Historical snapshots](docs/history/README.md) preserve prior evidence and plans;
they are not startup context or instructions to rerun old jobs.

## Local private pilot

The connected private executable/installer needs no local API, Python, Node or
model weights. Build details and remaining clean-install/signing gates:
[private desktop delivery](docs/PRIVATE_DESKTOP_DELIVERY.md).

In separate PowerShell terminals at the repository root:

```powershell
.\scripts\library.ps1 -Action server -TextFiles -AutoProcess
.\scripts\library.ps1 -Action frontend -TextFiles
```

Open http://localhost:1420/ -> Operator pilot. Use the existing test accounts;
never paste passwords/tokens into chat. The scripts reuse configured local
operator credentials, public configuration and the installed supported runtimes.
A fresh checkout requires the setup in [the desktop guide](apps/desktop/README.md)
and [hosted setup](docs/HOSTED_SUPABASE_SETUP.md); do not install/provision blindly.

Selection/preview stays local. Confirmed Save stores reviewed text in Supabase
Sydney; an opted-in automatic worker/search uses private CPU inference in Mumbai.
The current pilot supports UTF-8 TXT/Markdown, at most 64 KiB and three processing
passages. Failed inference requires explicit recovery; no public signup. Read
[private file handling](docs/PRIVATE_TEXT_FILES.md) before importing.

[Model connection diagnostics](docs/MODEL_AVAILABILITY.md) separate explicit
readiness checks from embeddings. A readiness GET may wake the cloud service;
pilot counters are not a billing meter. No end-user model weights are required.

## Checks and maintenance

Use project runtime scripts; do not rely on the outdated default Node in PATH.

```powershell
.\scripts\python.ps1 -m unittest tests.worker.test_search -q
.\scripts\desktop.ps1 build
.\scripts\python.ps1 scripts/audit_files.py --check-links
```

Choose focused checks from [the test plan](docs/TEST_PLAN.md); the full quality
command is `scripts/check.ps1`. Model benchmarks, Docker/SQL integration and
cloud probes are explicit operations, not routine prerequisites for documentation.

The read-only audit writes its inventory/reference report to ignored
`output/file-audit/current/`. It never deletes files. Its reference counts are
not usage telemetry or proof that an unreferenced file is unused.

Private documents, credentials, model caches and build outputs remain ignored.
Do not run [legacy prototypes](legacy/README.md) against personal documents.
Keep artifacts on D:, protect unrelated workloads, commit locally and push only
on explicit instruction. See [audit/retention policy](docs/FILE_AUDIT.md).
