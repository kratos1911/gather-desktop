# Obsidian project workflow

Return to [[docs/PROJECT_HUB]]. The repository itself is the vault: these notes
are the same files the development workflow reads and updates. No separate copy
or synchronization service is needed.

## Before working

Read the hub, current state, tasks and relevant linked design/decision notes.
Check user-authored notes for context. Draft ideas do not silently override the
latest user choices or accepted decisions. Keep ambiguous ideas labelled open.

## After each meaningful checkpoint

1. Update TASKS with acceptance evidence and unfinished work.
2. Update MEMORY with current status, limitations and next action.
3. Append PROGRESS with what changed, why, checks and remaining issues.
4. Add a DECISIONS entry when the architecture or scope changes.
5. Update the concept notes and flow canvas when the explanation changes.
6. Refresh the hub's checkpoint summary; keep detailed evidence in canonical notes.

Use [[docs/knowledge/templates/Work session|Work session template]] for a dated
session note. Notes do not replace tests. Never mark fixtures as semantic results
or report earlier checks as rerun.

## Vault configuration

Templates use docs/knowledge/templates; new daily notes use docs/knowledge/journal.
Existing daily notes and canvases are preserved. Configuration and workspace
state under .obsidian remain local and are excluded from Git. No community
plugins, paid service, publishing or sync configuration is added.

The application may need a reload to pick up externally edited configuration.
On-disk configuration and links can be checked here; visual behavior inside the
open Obsidian window has not been verified.

Obsidian supports internal Markdown links and wikilinks; see its
[official link documentation](https://obsidian.md/help/links) and
[vault configuration documentation](https://obsidian.md/help/Files%2Band%2Bfolders/Configuration%2Bfolder).
