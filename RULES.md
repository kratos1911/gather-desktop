# Development workflow

Read -> Understand -> Plan -> Implement -> Test -> Review -> Fix -> Commit ->
Update documentation. Follow AGENTS.md for the required short context set,
Windows/runtime rules, protected scope and handoff ownership.

## Task discipline

Select one reviewable task, its files and acceptance. Reuse current contracts;
avoid competing implementations, unrelated refactors and speculative features.
Ask only for material missing decisions, destructive scope, paid resources or
protected workload changes. Routine authorized work proceeds.

Learning preference: before a major milestone, ask at most one or two important
AI Engineer interview questions. Review answers strictly and briefly. Avoid
extended follow-up chains. When the user requests continuation, explain any
essential correction and proceed with authorized work.

Use statuses honestly: done requires verified acceptance; partial identifies
missing evidence; ready/blocked/deferred retain their actual meanings.
Fixtures are not semantic results; readiness is not embedding success.

## Verification and review

Use relevant TEST_PLAN/SECURITY gates. Check changed behavior and required
frontend builds; native rebuild only when native inputs/production assets change.
Reuse compatible fixtures, vectors and prior evidence. Expand checks only for
a concrete change/failure/risk. No model benchmarks or Docker by default for
documentation/UI work. Respect approvals; never bypass a rejection.

Review correctness, ownership/version/citation boundaries, cancellation,
privacy, accessibility, errors and resource limits. Diagnose two failed
environment attempts before another recovery approach; never repeat unchanged
RAM/Docker/runtime failures or weaken limits to pass.

## Git and release

Keep small local checkpoints after checks, using explicit staging paths and
reviewed diffs. Preserve unrelated/user-authored work. Never invent Git identity,
overwrite another writer, or infer push permission from "continue".
Use feature branches/worktrees only as appropriate to agreed ownership.
Deployment, new paid resources, telemetry or wider data access require their
applicable explicit approvals/release gates.

## One owner for each kind of context

- PRD: product goal/scope; ARCHITECTURE: current components/trust boundaries.
- DESIGN: visual rules/provenance; TASKS: current backlog and acceptance.
- MEMORY: current verified state, constraints, blockers and next task.
- PROGRESS: concise dated work/evidence; DECISIONS: durable rationale.
- PROJECT_HUB: topic navigation; history/: superseded plans/journals.

Update the matching current section instead of prepending repeated status.
Preserve detailed history under docs/history with dated unique filenames and
links. Consult it only for a historical question; ordinary searches exclude it
through .ignore. Do not treat historical commands/notes as current authorization.
The user's original generic workflow examples do not change Gather's stack.
