# SCUBA Ideaverse

**Your research world, mapped and connected.**

A research memory control panel for Obsidian vaults. Dock artifacts into reef channels, run **Quick Dip** to chart PDF facts, then **Deep Dive** to enrich — open the result in Obsidian.

## Quick start

```bash
./manager/scripts/dev.sh
```

Open **http://127.0.0.1:5173** → pick **Shallow reef** or **Blank reef** in the header.

## Workflow

1. **Pick a channel** on the Dive Computer (My Portfolio, Lit Review, Lab Memory, …)
2. **Dock** — drop files, **Confirm Upload** → `raw/{channel}/`
3. **Quick Dip** — runs automatically after portfolio upload; or click **Update chart (Quick Dip)**
4. **Deep Dive** — themes, one-liner, analysis in `builder/entries/` and `builder/deepdives/`
5. **Open reef in Obsidian**

See [docs/PAPER-CHART-SPEC.md](../docs/PAPER-CHART-SPEC.md) for Tier 1 vs Tier 2 rules.

## Docks

| Dock | `raw/` path | Chart |
|------|-------------|-------|
| ⚓ My Portfolio | `raw/papers/` | Quick Dip → `wiki/papers/` |
| 🌊 Literature Review | `raw/literature/` | Quick Dip → `wiki/sources/` |
| 🤿 Dive Log | `raw/dive-log/` | Quick Dip → `wiki/sources/` |
| 💡 Ideas & Notes | `raw/notes/inbox/` | Quick Dip → `wiki/sources/` |

Use **+ Add dock** in the UI to create custom folders. Config lives in `builder/docks.yaml` per vault.

## Dive Computer

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
| **Dive Computer** | Dashboard stats per channel |
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

Legacy aliases: `/airlock`, `/upload`, `/update-map`

## Team setup

See [docs/SCUBA-IDEAVERSE.md](../docs/SCUBA-IDEAVERSE.md) for the full guide.
