# Development workflow

For each task: **Read -> Understand -> Plan -> Implement -> Test -> Review -> Fix -> Commit -> Update documentation.** Documentation changes are included in the task commit; if they follow it, use a small follow-up commit. Never leave task status claiming unverified completion.

## Before coding

Read AGENTS.md, docs/PRD.md, docs/ARCHITECTURE.md, docs/DESIGN.md, this file, TASKS.md and docs/MEMORY.md. Read relevant security/test/decision notes. Inspect the existing code. State the selected task, scope and acceptance criteria in simple language.

## Task discipline

Implement one reviewable feature or prerequisite at a time. Prefer complete vertical user flows. Keep the current data private, changes scoped, boundaries explicit and TypeScript strict. Reuse components; avoid speculative abstractions and duplicated database layers. Explain significant decisions; routine authorized steps do not need repeated approval.

Use statuses: done (criteria verified), partial (implemented with missing evidence), ready, blocked (specific external dependency), deferred. Include evidence and limitations rather than marking a whole phase done when only UI exists.

## Verification and review

Run applicable type, lint, unit/integration/E2E and build checks. Do not claim checks exist or pass when tooling is absent. Choose tests for behavior and failure modes, not to mirror implementation. Review correctness, architecture, privacy, security, accessibility, errors and performance. Record issues, fix within scope, rerun affected checks. Separate visual/native QA from jsdom tests.

Use docs/TEST_PLAN.md and docs/SECURITY.md as gates. Respect previous denied tool permissions; do not bypass them through another tool.

## Git and release

User preference (27 September): commit locally as checkpoints, but push only on
an explicit user request to push. Do not infer push permission from "continue".

Use explicit staging paths and inspect staged files/diffs. Exclude secrets, personal files, model caches, environments and generated artifacts. Make small descriptive commits after checks. Use a feature branch for substantial subsequent work and review before merging. Do not invent Git identity or overwrite others' changes. Push/create remote repositories only with a known authorized destination.

Release through a test installer and QA before public distribution. Record release limitations, rollback and monitoring. No secrets/document content in logs; no silent paid dependencies, telemetry or model downloads.

## Documentation ownership

PRD = what/why; ARCHITECTURE = how; DESIGN = visual entry point; TASKS = work/evidence; DECISIONS = durable rationale; MEMORY = present state; PROGRESS = historical journal. PROJECT_BLUEPRINT is supporting detailed design/history, not an alternate current-state tracker.

Generic examples in the user's workflow guide are examples. They do not change the agreed desktop stack, prohibited designs, cost constraints or scope.
