# SCUBA Ideaverse

**Your research world, mapped and connected.**

A research memory control panel for Obsidian vaults. Dock artifacts into reef channels, surface structured charts, and navigate in Obsidian.

## Quick start

```bash
./manager/scripts/dev.sh
```

Open **http://127.0.0.1:5173**

## Workflow

1. **Pick a channel** on the Dive Computer (My Portfolio, Lit Review, Lab Memory, …)
2. **Dock** — drop files, **Confirm Upload** → `raw/{channel}/`
3. **Surface Interval** — update the chart for that channel
4. **Open reef in Obsidian**

## Reef channels

| Channel | `raw/` path | Surface interval |
|---------|-------------|------------------|
| My Portfolio | `raw/papers/` | Map → `builder/entries/` → build chart |
| Lab Portfolio | `raw/lab/papers/` | Map → `builder/entries/` → build chart |
| Literature Review | `raw/literature/` | Map → `builder/entries/` → `wiki/sources/` shells |
| Lab Memory | `raw/transcripts/` | Map → `builder/entries/` → `wiki/sources/` shells |
| Ideas & Notes | `raw/notes/inbox/` | Map → `builder/entries/` → `wiki/sources/` shells |

**Uploads stay in `raw/` only.** Chart scaffolds deterministic sections from `builder/templates/`
into `builder/entries/`. LLM **Deep Dive** (Phase 3+) fills generative sections in `builder/deepdives/`.

## Completion tracking

The Dive Computer reports:

| Stat | Meaning |
|------|---------|
| **On chart** | Entries in the registry (surfaced at least once) |
| **Processed** | Fully charted — themes, abstract, one-liner, and deep dive filled |
| **Needs review** | On chart but missing content (scaffolded or charted, not processed) |
| **Pending surface** | Files in `raw/` not yet mapped |

Per-channel cards list specific entries that need attention when selected.

## SCUBA vocabulary

| Term | Meaning |
|------|---------|
| **Dock** | Stage artifacts into a channel (no chart update) |
| **Channel** | A reef corpus — portfolio or ingest profile |
| **Chart** | Generated map (`wiki/` + `index.md`) |
| **Surface Interval** | Process channel → update chart |
| **Dive Computer** | Dashboard stats per channel |
| **Reef** | The Obsidian vault |

## API

| Method | Path |
|--------|------|
| POST | `/dock?vault_id=&channel_id=` |
| POST | `/surface_interval?vault_id=&channel_id=` |
| GET | `/channels` |
| GET | `/dive_computer` |

Legacy aliases: `/airlock`, `/upload`, `/update-map`

## Team setup

See [docs/SCUBA-IDEAVERSE.md](../docs/SCUBA-IDEAVERSE.md) for the full guide. Point `manager/backend/config/vaults.yaml` at your lab's vault path.
