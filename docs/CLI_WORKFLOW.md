# Gather desktop and CLI workflow

Use the CLI for scoped implementations, bug fixes and tests. Use the desktop
session for task selection, architecture decisions and independent review.
These roles can be exchanged explicitly; neither session is infallible.

## Start each handoff

1. Open the CLI in the Gather repository. Read AGENTS.md and its required notes.
2. Record branch, HEAD, git status and pre-existing changes. Do not clean them up.
3. Receive one task with outcome, allowed files, acceptance checks and exclusions.
4. Identify the writer and reviewer. Only the writer changes this checkout until
   it hands back. A document is coordination guidance, not a filesystem lock.
5. Check only the prerequisites needed for the task. Use scripts/python.ps1 for
   lightweight Python checks and scripts/desktop.ps1 for frontend commands.
   Model/inference work uses its established environment, not arbitrary Python.

## Task brief fields

- Outcome: one observable change.
- Writer/reviewer: explicit session ownership.
- Starting state: branch, commit and existing edits.
- Allowed files: include any required documentation; don't infer extra scope.
- Acceptance: behaviors and focused commands, plus required builds.
- Limits: D: artifacts, protected workloads, approvals and resource bounds.
- Delivery: diff summary, commands and exit codes, known gaps, suggested next step.
- Commit: reviewer by default; never push without explicit user instruction.

Use a short task-specific brief instead of pasting the whole chat. AGENTS.md and
canonical docs supply standing context. Read relevant notes once, then use
targeted searches. Do not weaken checks or use synthetic outputs as live evidence.

## Completion and review

The CLI reports results and stops editing. The user tells the desktop session the
task is done; this workflow does not automatically connect or message sessions.
The reviewer inspects git diff and untracked files, verifies meaningful changed
behavior, fixes or returns findings, then commits only intended paths locally.
The reviewer updates canonical docs/Obsidian links unless explicitly assigned to
the CLI. Preserve unrelated changes and avoid duplicate status files.

## Troubleshooting

After two failed environment attempts, identify the failure before trying again.
No whole-drive searches, guessed executable paths or repeated unchanged commands.
Never bypass an approval rejection. Report the exact blocked action and proceed
with independent work. Log temporary diagnostics under ignored output/ on D:.
Check child exit codes; launching a process does not prove its tests passed.

For simultaneous coding, agree on separate worktrees and integration steps first.
Do not share model runs, build output directories or protected services casually.
Persistent instructions reduce mistakes; they do not guarantee every task works.

Reference: [OpenAI project instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
