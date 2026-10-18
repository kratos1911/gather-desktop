# Project working rules

## Desktop and CLI collaboration

- Follow docs/CLI_WORKFLOW.md when a task is handed between sessions. Shared files do not mean shared conversation history.
- Use one writer at a time in this checkout. The other session may review but must not edit, commit, change branches or run resource-heavy checks concurrently. Parallel implementation needs separately agreed worktrees and integration ownership.
- Begin with branch, HEAD and working-tree status. Preserve pre-existing changes. Work only within the assigned file scope; report a missing prerequisite before expanding it.
- A delegated CLI task ends with changed files, actual commands/exit codes, limitations and proposed documentation updates. Leave it uncommitted unless the handoff explicitly assigns commit ownership. The reviewing session independently verifies before committing. This scopes the normal commit/documentation workflow for delegated tasks.

## Windows execution

- For lightweight Python checks use `./scripts/python.ps1 -m unittest <module>` in PowerShell. It resolves an installed interpreter without relying only on PATH and propagates the test exit code. `GATHER_PYTHON` can select an explicit interpreter. Model work still uses its dedicated runtime scripts.
- Use PowerShell commands (`Get-Content`, `Get-Command`, `where.exe`), not assumed Unix tools or the ambiguous `where` alias. Invoke quoted executable paths with `&` and keep arguments separate.
- After two failed environment attempts, diagnose the actual error before retrying. Never recursively scan whole drives for runtimes, repeatedly try unchanged commands, or install software to fix a discovery/quoting issue.
- Keep diagnostic files under ignored `output/` on D:, not the repository root. Report extra files honestly. Do not bypass approval rejections.

Read docs/PRD.md, docs/ARCHITECTURE.md, docs/DESIGN.md, RULES.md, TASKS.md and docs/MEMORY.md before changing this project. Read relevant test/security/decision notes and the supporting blueprint when needed. The latest user choices take priority over earlier design proposals.

Follow Read -> Understand -> Plan -> Implement -> Test -> Review -> Fix -> Commit -> Update documentation. Select one task and its acceptance criteria. Keep current status in MEMORY.md, work/evidence in TASKS.md, rationale in DECISIONS.md and historical updates in PROGRESS.md. Do not mark partial or unverified features complete.

- Build the desktop app in apps/desktop. Old Python scripts are archived in legacy; do not run or import them against personal documents during checks.
- Apply every item in docs/DESIGN_AVOID_LIST.md. Preserve licensing/provenance and distinguish inspiration from copied code or generated assets.
- Before adding accounts, uploads, telemetry, email or payments, consult docs/PRIVACY_RELEASE_AUDIT.md and close the relevant implementation gates. Do not invent contact details or claim legal compliance.
- Target cloud-hosted AI per the user's 27 September decision. Provider, budget and deployment are deferred; do not provision paid resources yet. Supabase Free remains the planned vector backend.
- Explain significant decisions in simple language. Record completed work, checks and unverified items in docs/PROGRESS.md.
- Never pass off fixtures as semantic results or sample animation as actual model work.
- Keep commits local. Push to GitHub only when the user explicitly asks to push; routine permission to continue development is not push authorization.
- Use docs/PROJECT_HUB.md and relevant Obsidian-linked notes as working references. Maintain the hub, concepts and flow map alongside canonical task/state/decision/progress documents. Preserve user-authored notes; label proposed ideas and unverified behavior explicitly.
- Test meaningful changed behavior and build the frontend. When native inputs/assets change, rebuild the desktop executable too.
