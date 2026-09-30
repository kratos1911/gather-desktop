# Project working rules

Read docs/PRD.md, docs/ARCHITECTURE.md, docs/DESIGN.md, RULES.md, TASKS.md and docs/MEMORY.md before changing this project. Read relevant test/security/decision notes and the supporting blueprint when needed. The latest user choices take priority over earlier design proposals.

Follow Read -> Understand -> Plan -> Implement -> Test -> Review -> Fix -> Commit -> Update documentation. Select one task and its acceptance criteria. Keep current status in MEMORY.md, work/evidence in TASKS.md, rationale in DECISIONS.md and historical updates in PROGRESS.md. Do not mark partial or unverified features complete.

- Build the desktop app in apps/desktop. Root Python scripts are legacy; do not run them against personal documents during checks.
- Apply every item in docs/DESIGN_AVOID_LIST.md. Preserve licensing/provenance and distinguish inspiration from copied code or generated assets.
- Before adding accounts, uploads, telemetry, email or payments, consult docs/PRIVACY_RELEASE_AUDIT.md and close the relevant implementation gates. Do not invent contact details or claim legal compliance.
- Target cloud-hosted AI per the user's 27 September decision. Provider, budget and deployment are deferred; do not provision paid resources yet. Supabase Free remains the planned vector backend.
- Explain significant decisions in simple language. Record completed work, checks and unverified items in docs/PROGRESS.md.
- Never pass off fixtures as semantic results or sample animation as actual model work.
- Keep commits local. Push to GitHub only when the user explicitly asks to push; routine permission to continue development is not push authorization.
- Use docs/PROJECT_HUB.md and relevant Obsidian-linked notes as working references. Maintain the hub, concepts and flow map alongside canonical task/state/decision/progress documents. Preserve user-authored notes; label proposed ideas and unverified behavior explicitly.
- Test meaningful changed behavior and build the frontend. When native inputs/assets change, rebuild the desktop executable too.
