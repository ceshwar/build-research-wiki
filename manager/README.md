# SCUBA Ideaverse

**Your research world, mapped and connected.**

A research memory control panel for Obsidian vaults. Dock artifacts into reef channels, run **Quick Dip** to chart PDF facts, then **Deep Dive** to enrich — open the result in Obsidian.

## Quick start

```bash
./manager/scripts/dev.sh
```

Open **http://127.0.0.1:5173** → pick **Shallow reef** or **Blank reef** in the header.

## Workflow

1. **Pick a dock** — hover pills for channel purpose; workspace opens on **Map**
2. **Workspace** — `Reef › Dock` path + tabs (Map · Chart status · Actions)
3. **Dock** — click dock name in path or **Upload PDFs** in Actions
4. **Chart status** — track on chart / quick dip / enrich next for this dock
5. **Map** — List or By theme (portfolio); expand **Note** for one-liner + PDF; toggle **Edit** to remove papers from the chart
6. **Actions** — **Update chart** or **Get ingest prompt** for Deep Dive
7. **Open reef in Obsidian**

See [docs/PAPER-CHART-SPEC.md](../docs/PAPER-CHART-SPEC.md) for Tier 1 vs Tier 2 rules.

## Docks

| Dock | `raw/` path | Chart |
|------|-------------|-------|
| ⚓ My Portfolio | `raw/papers/` | Quick Dip → `wiki/papers/` |
| 🌊 Literature Review | `raw/literature/` | Quick Dip → `wiki/sources/` |
| 🤿 Dive Log | `raw/dive-log/` | Quick Dip → `wiki/sources/` |
| 💡 Ideas & Notes | `raw/notes/inbox/` | Quick Dip → `wiki/sources/` |

Hover a dock pill in the picker for its description. Use **+ Add dock** to create custom folders. Config lives in `builder/docks.yaml` per vault.

## Focused workspace

Selecting a dock hides the dock picker and shows one shell:

| Tab | Purpose |
|-----|---------|
| **Map** | List (sortable) or By theme (portfolio); **Note** + PDF per paper; **Edit** to remove rows |
| **Chart status** | Pipeline stats, next-step banner; stat cards filter Map |
| **Actions** | Update chart, Get ingest prompt, upload shortcut |

Click the **dock name** in the path (`Reef › Dock`) to switch docks or upload. The onboarding guide dismisses per reef (browser `localStorage`).

## Chart status stats

| Stat | Meaning |
|------|---------|
| **On chart** | Artifacts already on your wiki chart |
| **Awaiting chart** | Uploaded to a dock folder, not charted yet (run Update chart) |
| **Quick dip** | Tier 1 done — PDF facts extracted |
| **Enrich next** | On chart but needs Deep Dive (themes, analysis) |

**Chart updated** (top right) = when the wiki was last rebuilt — not a count.

## SCUBA vocabulary

| Term | Meaning |
|------|---------|
| **Dock** | Stage artifacts into a channel (no chart update) |
| **Quick Dip** | Tier 1 chart update — PDF facts only |
| **Deep Dive** | Tier 2+ enrichment (themes, analysis) |
| **Channel** | A reef corpus — portfolio or ingest profile |
| **Chart** | Generated map (`wiki/` + `index.md`) |
| **Chart status** | Per-dock charting tracker |
| **Map** | Browse chart for the active dock |
| **Reef** | The Obsidian vault |

## API

| Method | Path |
|--------|------|
| POST | `/dock?vault_id=&channel_id=` |
| POST | `/surface_interval?vault_id=&channel_id=` |
| GET | `/channels?vault_id=` |
| POST | `/vaults/{id}/docks` — create custom dock |
| GET | `/vaults` |
| GET | `/chart-map?vault_id=&channel_id=` |
| POST | `/vaults` — add reef `{ path, name? }` |
| POST | `/vaults/validate` — check folder |
| POST | `/vaults/pick-folder` — native folder picker |
| DELETE | `/vaults/{id}` — remove user-added reef |
| DELETE | `/chart-entry?vault_id=&channel_id=&slug=` — remove paper from map (PDF stays in dock) |

Legacy aliases: `/airlock`, `/upload`, `/update-map`

## Team setup

See [docs/TEAM-COLLABORATION.md](../docs/TEAM-COLLABORATION.md).
