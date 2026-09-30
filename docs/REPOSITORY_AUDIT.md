# Repository cleanup audit

30 September 2026. Inventory covers every Git-tracked file at the start of this
cleanup. Read all tracked file bytes and parsed Python source without importing
or running legacy code; reviewed runtime entry points and searched references.
This is a necessity/organization audit, not a full correctness or security audit.

## Changes

Archived six old root files unchanged in legacy/ with a warning README. Removed
three unreferenced starter logos and the root macOS .DS_Store metadata file.
Kept app code, worker code, tests, fixtures, lockfiles, notices, build setup,
native icon variants and documents. Historical notes keep their original paths.

## Local files deliberately preserved

.env, original documents, databases/indexes, model environments, output artifacts,
Obsidian settings and Untitled.canvas are not disposable code. Their contents
were not opened for this cleanup. Dependency/build/cache directories are generated
or needed for current development and were not recursively purged. Git history
is retained. No personal data was imported, uploaded or deleted.

## Per-file disposition

| Original tracked path | Action | Reason |
| --- | --- | --- |
| `.env.example` | Keep | Repository configuration, onboarding or workflow rules |
| `.github/workflows/quality.yml` | Keep | Repository configuration, onboarding or workflow rules |
| `.gitignore` | Keep | Repository configuration, onboarding or workflow rules |
| `AGENTS.md` | Keep | Repository configuration, onboarding or workflow rules |
| `README.md` | Keep | Repository configuration, onboarding or workflow rules |
| `RULES.md` | Keep | Repository configuration, onboarding or workflow rules |
| `TASKS.md` | Keep | Repository configuration, onboarding or workflow rules |
| `apps/desktop/.gitignore` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/.vscode/extensions.json` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/README.md` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/eslint.config.mjs` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/index.html` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/package-lock.json` | Keep | Reproducible dependency resolution |
| `apps/desktop/package.json` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/public/THIRD_PARTY_NOTICES.txt` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/public/contours.svg` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/public/tauri.svg` | Remove | Unused scaffold artwork; no active references |
| `apps/desktop/public/vite.svg` | Remove | Unused scaffold artwork; no active references |
| `apps/desktop/scripts/frontend.mjs` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/src-tauri/.gitignore` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/src-tauri/Cargo.lock` | Keep | Reproducible dependency resolution |
| `apps/desktop/src-tauri/Cargo.toml` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/src-tauri/build.rs` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/src-tauri/capabilities/default.json` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/src-tauri/icons/128x128.png` | Keep | Native platform artwork; preserve packaging variants |
| `apps/desktop/src-tauri/icons/128x128@2x.png` | Keep | Native platform artwork; preserve packaging variants |
| `apps/desktop/src-tauri/icons/32x32.png` | Keep | Native platform artwork; preserve packaging variants |
| `apps/desktop/src-tauri/icons/Square107x107Logo.png` | Keep | Native platform artwork; preserve packaging variants |
| `apps/desktop/src-tauri/icons/Square142x142Logo.png` | Keep | Native platform artwork; preserve packaging variants |
| `apps/desktop/src-tauri/icons/Square150x150Logo.png` | Keep | Native platform artwork; preserve packaging variants |
| `apps/desktop/src-tauri/icons/Square284x284Logo.png` | Keep | Native platform artwork; preserve packaging variants |
| `apps/desktop/src-tauri/icons/Square30x30Logo.png` | Keep | Native platform artwork; preserve packaging variants |
| `apps/desktop/src-tauri/icons/Square310x310Logo.png` | Keep | Native platform artwork; preserve packaging variants |
| `apps/desktop/src-tauri/icons/Square44x44Logo.png` | Keep | Native platform artwork; preserve packaging variants |
| `apps/desktop/src-tauri/icons/Square71x71Logo.png` | Keep | Native platform artwork; preserve packaging variants |
| `apps/desktop/src-tauri/icons/Square89x89Logo.png` | Keep | Native platform artwork; preserve packaging variants |
| `apps/desktop/src-tauri/icons/StoreLogo.png` | Keep | Native platform artwork; preserve packaging variants |
| `apps/desktop/src-tauri/icons/icon.icns` | Keep | Native platform artwork; preserve packaging variants |
| `apps/desktop/src-tauri/icons/icon.ico` | Keep | Native platform artwork; preserve packaging variants |
| `apps/desktop/src-tauri/icons/icon.png` | Keep | Native platform artwork; preserve packaging variants |
| `apps/desktop/src-tauri/src/lib.rs` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/src-tauri/src/main.rs` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/src-tauri/tauri.conf.json` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/src/App.css` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/src/App.test.tsx` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/src/App.tsx` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/src/assets/react.svg` | Remove | Unused scaffold artwork; no active references |
| `apps/desktop/src/components/Interactions.tsx` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/src/components/PolicyPage.tsx` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/src/fixtures.ts` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/src/main.tsx` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/src/vite-env.d.ts` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/tsconfig.json` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/tsconfig.node.json` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/vite.config.ts` | Keep | Desktop source, build configuration or retained assets |
| `apps/desktop/vitest.config.ts` | Keep | Desktop source, build configuration or retained assets |
| `chroma.py` | Archive in legacy/ | Historical prototype; not imported by active app/worker |
| `code_reader.py` | Archive in legacy/ | Historical prototype; not imported by active app/worker |
| `docs/ARCHITECTURE.md` | Keep | Requirements, evidence, design or historical context |
| `docs/BOOKMARKS.md` | Keep | Requirements, evidence, design or historical context |
| `docs/DECISIONS.md` | Keep | Requirements, evidence, design or historical context |
| `docs/DESIGN.md` | Keep | Requirements, evidence, design or historical context |
| `docs/DESIGN_AVOID_LIST.md` | Keep | Requirements, evidence, design or historical context |
| `docs/DESIGN_DIRECTION.md` | Keep | Requirements, evidence, design or historical context |
| `docs/MEMORY.md` | Keep | Requirements, evidence, design or historical context |
| `docs/MODEL_STRATEGY.md` | Keep | Requirements, evidence, design or historical context |
| `docs/PRD.md` | Keep | Requirements, evidence, design or historical context |
| `docs/PRIVACY_RELEASE_AUDIT.md` | Keep | Requirements, evidence, design or historical context |
| `docs/PROGRESS.md` | Keep | Requirements, evidence, design or historical context |
| `docs/PROJECT_BLUEPRINT.md` | Keep | Requirements, evidence, design or historical context |
| `docs/PROJECT_HUB.md` | Keep | Requirements, evidence, design or historical context |
| `docs/SECURITY.md` | Keep | Requirements, evidence, design or historical context |
| `docs/TEST_PLAN.md` | Keep | Requirements, evidence, design or historical context |
| `docs/knowledge/AGENT_REACH.md` | Keep | Requirements, evidence, design or historical context |
| `docs/knowledge/EXTRACTION_STACK.md` | Keep | Requirements, evidence, design or historical context |
| `docs/knowledge/IDEAS_AND_QUESTIONS.md` | Keep | Requirements, evidence, design or historical context |
| `docs/knowledge/OBSIDIAN_WORKFLOW.md` | Keep | Requirements, evidence, design or historical context |
| `docs/knowledge/SEARCH_CONCEPTS.md` | Keep | Requirements, evidence, design or historical context |
| `docs/knowledge/Search flow.canvas` | Keep | Requirements, evidence, design or historical context |
| `docs/knowledge/journal/2026-09-30.md` | Keep | Requirements, evidence, design or historical context |
| `docs/knowledge/templates/Idea.md` | Keep | Requirements, evidence, design or historical context |
| `docs/knowledge/templates/Work session.md` | Keep | Requirements, evidence, design or historical context |
| `main.py` | Archive in legacy/ | Historical prototype; not imported by active app/worker |
| `main1.py` | Archive in legacy/ | Historical prototype; not imported by active app/worker |
| `prompts.py` | Archive in legacy/ | Historical prototype; not imported by active app/worker |
| `requirements.txt` | Archive in legacy/ | Historical prototype; not imported by active app/worker |
| `scripts/check.ps1` | Keep | Verification fixtures, evaluation or developer tooling |
| `scripts/desktop.ps1` | Keep | Verification fixtures, evaluation or developer tooling |
| `scripts/evaluate_vectors.py` | Keep | Verification fixtures, evaluation or developer tooling |
| `scripts/prepare_text_evaluation.py` | Keep | Verification fixtures, evaluation or developer tooling |
| `scripts/score_text_evaluation.py` | Keep | Verification fixtures, evaluation or developer tooling |
| `services/worker/EMBEDDING_CLIENT.md` | Keep | Active worker implementation or its contract |
| `services/worker/README.md` | Keep | Active worker implementation or its contract |
| `services/worker/__init__.py` | Keep | Active worker implementation or its contract |
| `services/worker/bookmarks.py` | Keep | Active worker implementation or its contract |
| `services/worker/embedding_client.py` | Keep | Active worker implementation or its contract |
| `services/worker/text_processing.py` | Keep | Active worker implementation or its contract |
| `tests/evaluation/BASELINE.md` | Keep | Verification fixtures, evaluation or developer tooling |
| `tests/evaluation/README.md` | Keep | Verification fixtures, evaluation or developer tooling |
| `tests/evaluation/VECTORS.md` | Keep | Verification fixtures, evaluation or developer tooling |
| `tests/evaluation/test_corpus.py` | Keep | Verification fixtures, evaluation or developer tooling |
| `tests/evaluation/test_scoring.py` | Keep | Verification fixtures, evaluation or developer tooling |
| `tests/evaluation/test_vectors.py` | Keep | Verification fixtures, evaluation or developer tooling |
| `tests/evaluation/text-v1.json` | Keep | Verification fixtures, evaluation or developer tooling |
| `tests/fixtures/text/receipt.txt` | Keep | Verification fixtures, evaluation or developer tooling |
| `tests/fixtures/text/study.md` | Keep | Verification fixtures, evaluation or developer tooling |
| `tests/worker/test_bookmarks.py` | Keep | Verification fixtures, evaluation or developer tooling |
| `tests/worker/test_embedding_client.py` | Keep | Verification fixtures, evaluation or developer tooling |
| `tests/worker/test_text_processing.py` | Keep | Verification fixtures, evaluation or developer tooling |
