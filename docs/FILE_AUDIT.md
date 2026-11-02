# File roles and retention audit

31 October interface addition: Library.tsx/.css/.test.tsx own the connected
screen and synthetic integration coverage; docs/UNIFIED_LIBRARY.md owns its
contract/provenance. OperatorPilot remains a regression harness used by its
discovered tests, not an application route. Do not delete it by reference count
alone. The original inventory totals below remain a dated snapshot.

PDF additions have distinct roles: pdf_processing.py and requirements-pdf.lock
own the parser boundary/provenance; migration13 and PDF tests protect storage
and page contracts. Stage/update helpers are explicit manual entry points.
PDF_IMPORT.md and WINDOWS_INSTALL_QA.md are linked from the hub. Retain them;
generated fixtures, receipts, wheels and packages stay ignored under output/.

Performance additions: database_session.py owns worker-only framed helpers;
processing_timing.py owns the numeric allowlist. benchmark_processing.py is an
explicit operator comparison entry point; check_worker_runtime.py is restricted
to disposable loopback/Linux fixtures and refuses Cloud Run startup. The hub links
PROCESSING_SPEED.md. Keep these manual/discovered contracts; benchmark receipts
and staged build contexts remain ignored under output/processing-speed/.

Audit snapshot: feature checkpoint `53cf9d8`, 26 October 2026. Reorganization
changes context/maintenance only, not application behavior. This is a necessity,
reference and navigation audit, not proof that all code is correct or secure.

## What was inspected

All **418 initially tracked files**: size/role, bounded text inspection, Python
syntax without imports/execution, Python/local TypeScript import edges, literal
incoming references, and local Markdown/Obsidian links. No whole-drive scan,
chat-history reload, model invocation, Docker or cloud operation. References are
static approximations, not observed runtime/read-frequency telemetry.

| Initial role | Files | Decision |
| --- | ---: | --- |
| Required current context | 7 | Keep paths stable; shorten current state/design/tasks |
| Application/build inputs | 143 | Keep; includes convention-loaded assets/configuration |
| Tests/frozen evidence | 122 | Keep; discovery/fixtures are not obsolete for lacking text references |
| Ordered migrations | 9 | Keep immutable history/order; never infer unused from latest schema |
| Operator/maintenance entry points | 44 | Keep manual tools and module launchers |
| Locked inputs/notices | 11 | Keep reproducibility, licensing and security provenance |
| Build/deployment/CI | 10 | Keep explicitly/manual-triggered configuration |
| Reference/knowledge docs | 54 | Keep contracts, evidence and future-slice requirements; read by topic |
| Archived prototype | 7 | Keep as historical source; never execute against personal data |
| Repository configuration/entry points | 11 | Keep; role is not determined by import count |

No functional source was proven redundant enough to delete. Empty package
markers, repeated distribution notices and identical bytes can have distinct
required roles. Zero literal references alone is not deletion approval.

## Daily context versus reference

The mandatory set remains AGENTS, RULES, PRD, ARCHITECTURE, DESIGN, TASKS and
MEMORY. It is read once per task. PROJECT_HUB now routes to the relevant module
contract; no full chat/all-doc/archive scan is needed for routine coding.

README/PRD/ARCHITECTURE now distinguish the verified private browser pilot from
the sample-only native app and gated general release. TASKS retains every task
ID with current status/acceptance. MEMORY is current-only; PROGRESS records dated
work; DECISIONS retains ADR rationale and is consulted selectively.

Five full superseded journals (258,338 original bytes) are preserved under
[history](history/README.md) with unique dated filenames. Prose/headings remain;
relative Markdown links were adjusted. Original byte-identical copies and hashes
are in `output/file-audit/recovery` and `archive-manifest.json`, and the original
tracked versions remain at checkpoint `53cf9d8`. Historical instructions are not
current authority. `.ignore` excludes history from ordinary ripgrep, not Git or
explicit reading; use `rg --no-ignore` for a historical question.

## Removed from working folders

Hash-verified recovery copies precede each removal. Only these seven files and
the resulting empty root cache directory were removed (18,210 bytes in total):

- `error.txt`: obsolete 608-byte console capture; only historical notes referred
  to preserving it, with no active code/config consumer. No log contents printed.
- `output.txt`: empty obsolete console capture.
- Root `__pycache__/chroma.cpython-313.pyc`, `code_reader.cpython-313.pyc`,
  `main.cpython-310.pyc`, `main.cpython-313.pyc`, `prompts.cpython-313.pyc`:
  generated orphan bytecode with no corresponding source at the root.

Recovery/removed-file hashes: `output/file-audit/removed-manifest.json`.
These are removals from working folders, not claimed net disk savings: recovery
copies intentionally remain in ignored output until separately reviewed.

Preserved without deletion: user-authored untracked `docs/MEMORY_CAPSULE.md`,
`.env`, private data/indexes/documents, Obsidian settings, model caches/weights,
configured environments, dependencies, native/build artifacts and runtime/test
receipts. Ignored private directories were not recursively inspected. No shared
Docker cache, running app/API or unrelated project was modified.

## Measurements and verification

| Required context | Before | After |
| --- | ---: | ---: |
| UTF-8 file bytes | 134,772 | 28,608 |
| Normalized text characters | 133,241 | 28,359 |

This is a **78.8% reduction in required-context file bytes**. It is not a
measurement of billed tokens or credit savings. Complete inventory/reference
examples: `output/file-audit/final/summary.json` and `inventory.csv`.

There are 427 tracked entries after organization versus 418 before: five
preserved snapshots, their index, the audit report, read-only auditor and search
default file are intentional additions. No application code, test, migration or
locked input was removed to make a file-count target.

### Reference observations

In the post-organization report, current non-history literal references most
often point to TASKS (23 source files), MEMORY (12), PRIVACY_RELEASE_AUDIT (10),
MODEL_AVAILABILITY/PRIVATE_TEXT_FILES (8 each) and INGESTION_COORDINATOR (7).
These are textual-reference counts, not actual task-read frequency. The explicit
seven-file AGENTS read set is the authoritative repeated work entry point.

Static import references identify runtime.py (32 source/test files),
service_transport.py (22), service_clients.py (19), cloud_identity.py (14) and
ingestion_repository.py (13) as shared dependencies. 115 tracked files have no
literal filename reference; their roles/imports/discovery still justify retention.
No byte-identical groups were found in the bounded (<=2 MiB/file) hash scan.
The detailed CSV records every file, ambiguity and reference examples.

Before reorganization: no local-link or Python-syntax errors in the tracked set.
Final checks passed: every tracked file classified, archive/recovery hashes match,
local Markdown/Obsidian links resolve, no Python syntax errors, correct default
history exclusion, and required frontend build (production JS hash unchanged). No model benchmark or broad
application regression rerun is warranted for unchanged application sources.

## Repeatable maintenance

scripts/verify_desktop_bundle.py is a manual, read-only Windows packaging entry
point. Its synthetic tests belong to normal unittest discovery. Retain both:
NSIS patches Tauri's bundle marker, so an installed executable has a different
raw hash from its verified unbundled input. Windows test receipts, installer
copies, browser profiles and install products stay under ignored output/.

```powershell
.\scripts\python.ps1 scripts/audit_files.py --check-links
```

This command never deletes, imports code, installs anything or scans ignored
private/model directories. Inspect the CSV for current/historical literal
references, static import references and role. Review dynamic/configuration/
discovery/manual use before any future deletion. Generated reports belong in
output; keep current docs concise and preserve history/evidence deliberately.
