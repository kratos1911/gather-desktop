# Personal knowledge library

A Windows desktop application being rebuilt to find saved content by meaning and answer questions about selected documents with source citations.

**Current status: interface foundation and offline processing.** The application
in `apps/desktop` shows labelled synthetic content. `services/worker` contains
tested TXT/Markdown processing, bookmark extraction and a mocked embedding client.
Real import, embeddings, Supabase and model inference are not connected. Chat is
deferred. Old scripts are preserved in [legacy](legacy/README.md); original data
folders and secrets remain untouched.

## Start here

- [Product requirements](docs/PRD.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Design entry point](docs/DESIGN.md)
- [Development rules](RULES.md)
- [Tasks and next acceptance criteria](TASKS.md)
- [Current state](docs/MEMORY.md)
- [Decision log](docs/DECISIONS.md)
- [Test plan](docs/TEST_PLAN.md)
- [Security requirements](docs/SECURITY.md)

Each task follows read, plan, implement, test, review, fix, commit and documentation updates. The desktop stack remains unchanged. `.env.example` lists future public configuration only; the preview does not read it yet.

- [Desktop run instructions](apps/desktop/README.md)
- [Project blueprint and milestones](docs/PROJECT_BLUEPRINT.md)
- [Model choices and benchmark plan](docs/MODEL_STRATEGY.md)
- [Design direction](docs/DESIGN_DIRECTION.md)
- [Progress and verification](docs/PROGRESS.md)

From PowerShell in this folder:

```powershell
./scripts/desktop.ps1 desktop
```

For a fresh checkout, install the prerequisites in the desktop instructions and run `./scripts/desktop.ps1 install` first. The helper avoids the broken npm shim detected on the development machine without modifying global PATH.

## Intended stack

Tauri + React + TypeScript, an authenticated cloud service with Python processing workers, and Supabase Auth/Storage/Postgres with pgvector. Starting model candidates remain EmbeddingGemma, SigLIP 2, Qwen3.5 and PaddleOCR, subject to cloud evaluation. Provider, framework, queue and deployment are deferred decisions.

The user selected cloud AI on 27 September: no end-user model downloads are planned. Hosting budget is undecided and no paid resources are authorized yet. Supabase Free remains the planned vector backend. See ADR-009.

## Processing tests

With Python 3.11 or newer, run `python -m unittest discover -s tests/worker -v` from this folder. See [the processing contract](services/worker/README.md) for input limits, offset semantics and recovery behavior. These tests use synthetic content only.

The [retrieval development set](tests/evaluation/README.md) contains 14 fictional
documents and 40 questions with expected source evidence. Run
`python -m unittest discover -s tests/evaluation -v` to validate it, or
`python -m scripts.prepare_text_evaluation` for its inventory. No model accuracy
is claimed from these integrity checks.

Run `python -m scripts.score_text_evaluation` for the offline keyword baseline
and scoring report. See [baseline results and limitations](tests/evaluation/BASELINE.md).
This comparator is not connected to the desktop and performs no AI/cloud calls.

## Repository hygiene

Open [the project hub](docs/PROJECT_HUB.md) in Obsidian for linked progress,
tasks, architecture, search concepts, decisions and the search-flow canvas.

Run `./scripts/check.ps1` for the local quality checks (Python 3.11+ required;
optional `-Python` selects its executable). This covers worker/evaluation/UI
tests, lint, types, formatting and frontend build. The manual GitHub workflow
has not been executed remotely; native runtime verification is separate.

[Links and bookmarks](docs/BOOKMARKS.md) are now planned alongside files:
save URLs and notes, extract available metadata/readable text, then reuse search
and selected-source chat. Saving a video URL does not imply understanding its
video. Bookmark implementation is pending.

Private files, model indexes, secrets, local Python environments and build outputs are ignored by `.gitignore`. Do not force-add those paths. No original files are automatically imported into the new app or uploaded to a cloud service.

- [Design avoid list](docs/DESIGN_AVOID_LIST.md)
- [Privacy and release audit](docs/PRIVACY_RELEASE_AUDIT.md)
