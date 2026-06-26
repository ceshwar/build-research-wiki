# Portolan

**Read what you dock. Chart the connections.**

Built for reading, in a world built for writing — Portolan keeps you oriented as the ocean of research keeps rising. The research assistant that actually reads your papers.

A research memory control panel for Obsidian vaults. Dock artifacts into reef channels, **Update chart** (Uncharted), run **Quick Dip** (LLM), review to **Deep dive** — browse in-app or Obsidian.

## Quick start

```bash
./manager/scripts/dev.sh
```

Open **http://127.0.0.1:5173** → pick **Shallow reef** or **Blank reef** in the header.

## Workflow

1. **Pick a dock** — hover pills for channel purpose; workspace opens on **Navigate**
2. **Workspace** — `Reef › Dock` path + tabs (Navigate · Status · Actions)
3. **Dock** — click dock name in path or **Upload PDFs** in Actions
4. **Status** — Uncharted · Quick dip · Deep dive for this dock
5. **Navigate** — List, By theme, or Graph; filters: All · Deep dive · Quick dip · Uncharted
6. **Actions** — **Update chart** and **Run Quick Dip (LLM)**
7. **Query** — ask the wiki with scope filters

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
| **Navigate** | List (sortable), By theme (portfolio), or Graph; **Edit** → mark **−** → **Done** / **Cancel** |
| **Status** | Pipeline stats, next-step banner; stat cards filter Navigate |
| **Actions** | Update chart, Run Quick Dip (LLM), upload shortcut |

Click the **dock name** in the path (`Reef › Dock`) to switch docks or upload. The onboarding guide dismisses per reef (browser `localStorage`).

## Status stats

| Stat | Meaning |
|------|---------|
| **On chart** | Artifacts already on your wiki chart |
| **Awaiting chart** | Uploaded to a dock folder, not charted yet (run Update chart) |
| **Uncharted** | On chart, not LLM-ingested yet |
| **Quick dip** | LLM-ingested — needs human review |
| **Deep dive** | Human-verified (or trusted hand-charted) |

**Chart updated** (top right) = when the wiki was last rebuilt — not a count.

## Key terms

| Term | Meaning |
|------|---------|
| **Dock** | Stage artifacts into a channel (no chart update) |
| **Uncharted** | Metadata on chart; no LLM pass yet |
| **Quick Dip** | LLM ingestion — needs review |
| **Deep Dive** | Verified, human-reviewed content |
| **Channel** | A reef corpus — portfolio or ingest profile |
| **Chart** | Generated map (`wiki/` + `index.md`) |
| **Status** | Per-dock pipeline tracker |
| **Navigate** | Browse chart for the active dock |
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
| GET | `/chart-graph?vault_id=&channel_id=` |
| GET | `/vault-file?vault_id=&path=` — in-app markdown viewer |
| POST | `/deep-dive?vault_id=&channel_id=` — LLM Deep Dive `{ slug \| slugs }` |
| POST | `/query?vault_id=` — wiki Q&A `{ question }` |
| GET | `/query/{job_id}` — query result when job completes |
| GET/PATCH | `/settings` — viewer, Ollama URL, models, local/frontier |
| GET | `/llm-config` |
| POST | `/chart-entry/verification?...` — mark human verified |
| GET | `/ingest-prompt?vault_id=&channel_id=` |
| POST | `/vaults` — add reef `{ path, name? }` |
| POST | `/vaults/validate` — check folder |
| POST | `/vaults/pick-folder` — native folder picker |
| DELETE | `/vaults/{id}` — remove user-added reef |
| DELETE | `/chart-entry?vault_id=&channel_id=&slug=` — remove one paper from chart |
| POST | `/chart-remove?vault_id=&channel_id=` — batch remove `{ "slugs": [...] }` |

Legacy aliases: `/airlock`, `/upload`, `/update-map`

## Team setup

See [docs/TEAM-COLLABORATION.md](../docs/TEAM-COLLABORATION.md).
