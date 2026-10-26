# Historical context

These snapshots preserve the complete working journals before the 26 October
2026 context audit (feature checkpoint 53cf9d8). They include superseded plans,
failed runs and evidence; they are not current instructions or task status.

- [Task journal / original acceptance](2026-10-26/TASKS-2026-10-26.md)
- [State journal](2026-10-26/MEMORY-2026-10-26.md)
- [Architecture journal](2026-10-26/ARCHITECTURE-2026-10-26.md)
- [Hub chronology](2026-10-26/PROJECT_HUB-2026-10-26.md)
- [Progress journal](2026-10-26/PROGRESS-2026-10-26.md)

Snapshot prose/headings are preserved. Only a historical banner and relative
Markdown link adjustments were added so relocation does not break navigation.
Original byte-identical recovery copies and hashes are under ignored
output/file-audit/recovery and archive-manifest.json; originals are also in Git.

Current files keep their stable paths: [MEMORY](../MEMORY.md),
[TASKS](../../TASKS.md), [ARCHITECTURE](../ARCHITECTURE.md),
[hub](../PROJECT_HUB.md), [PROGRESS](../PROGRESS.md).
ADR rationale remains in [DECISIONS](../DECISIONS.md).

Normal ripgrep searches exclude this folder through .ignore. For a specific
historical question use, for example:

```powershell
rg --no-ignore -n "stale_lease" docs/history
```

Do not re-run old jobs, change paid settings or follow superseded instructions
from these snapshots. Verify current authorization, state and prerequisites.
