# Personal knowledge library

A Windows desktop application being rebuilt to find saved content by meaning and answer questions about selected documents with source citations.

**Current status: step 1, interface foundation.** The new application is in `apps/desktop`. It shows clearly labelled synthetic content. Real import, embeddings, Supabase and model inference are not connected yet. The root Python scripts remain legacy; the privacy audit removed remote preview requests and sensitive console output. Original data folders remain untouched.

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

Tauri + React + TypeScript, a local Python processing worker, Supabase Auth/Storage/Postgres with pgvector, and locally executed models. Starting candidates: EmbeddingGemma 300M (text search), SigLIP 2 Base (photos), Qwen3.5 4B (chat/vision) and PaddleOCR PP-OCRv5 (scanned text). Quantization, model versions, dimensions and runtime performance remain benchmark decisions.

The service budget is zero recurring fees. Supabase free-tier capacity is finite and search needs connectivity. Model downloads and device hardware requirements will be explicit during setup.

## Repository hygiene

Private files, model indexes, secrets, local Python environments and build outputs are ignored by `.gitignore`. Do not force-add those paths. No original files are automatically imported into the new app or uploaded to a cloud service.

- [Design avoid list](docs/DESIGN_AVOID_LIST.md)
- [Privacy and release audit](docs/PRIVACY_RELEASE_AUDIT.md)
