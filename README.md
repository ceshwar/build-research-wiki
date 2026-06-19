# build-research-wiki

Build your own **LLM-powered research wiki** — a persistent, compounding knowledge base that
an AI assistant maintains for you. Drop in papers and notes; browse the result in
[Obsidian](https://obsidian.md).

**Based on the [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)** by Andrej Karpathy — compile knowledge once and keep it current.

---

## SCUBA Ideaverse (v0.3)

**Your research world, mapped and connected.**

A web control panel for docking artifacts, **Quick Dip** (Tier 1 PDF facts on chart), **Deep Dive** enrichment, and tracking completion in the Dive Computer.

```bash
./manager/scripts/dev.sh    # → http://127.0.0.1:5173
```

| Step | Action |
|------|--------|
| 1 | Pick a channel (portfolio, lit review, lab memory, …) |
| 2 | **Dock** files → `raw/{channel}/` (portfolio uploads auto-run Quick Dip) |
| 3 | **Update chart (Quick Dip)** → PDF facts → `builder/entries/` → `wiki/` |
| 4 | **Deep Dive** — edit `builder/entries/` and `builder/deepdives/`; re-chart |
| 5 | Open reef in Obsidian |

Full guide: **[docs/SCUBA-IDEAVERSE.md](docs/SCUBA-IDEAVERSE.md)** · Chart spec: **[docs/PAPER-CHART-SPEC.md](docs/PAPER-CHART-SPEC.md)**

---

## Three ways to use it

### 1. SCUBA Ideaverse (UI) — *recommended for teams*

Dock → Quick Dip → Deep Dive → Obsidian. Uploads stay in `raw/`; Tier 1 chart entries land in `builder/entries/` from PDF facts only (no guessing). The Dive Computer shows **Quick dip**, **Needs deep dive**, and **Deep dive done** counts.

### 2. LLM-driven ingest (agent workflow)

Drop documents into `raw/`, open the folder in Cursor or Claude Code, and say:

> *"Ingest the new papers in `raw/`."*

The assistant reads [`CLAUDE.md`](CLAUDE.md) and writes `wiki/sources/`, entities, concepts, syntheses. See [`CLAUDE.md`](CLAUDE.md) §6.

### 3. Deterministic builder (CLI / cron)

For a **paper portfolio mapped by research theme**, run `python3 builder/build.py`. Idempotent, scriptable. See [BUILD.md](BUILD.md).

You can combine all three: SCUBA for docking and chart scaffolding, the agent for deep dives and ingest, the builder for reproducible rebuilds.

---

## Quickstart

```bash
git clone https://github.com/ceshwar/build-research-wiki.git
cd build-research-wiki

# Option A — try the UI + demo vault
./manager/scripts/dev.sh

# Option B — browse the tour vault in Obsidian
open examples/minimal-vault   # or: File → Open vault in Obsidian

# Option C — start your own vault
python3 builder/new_vault.py ~/my-research-wiki "My Lab"
```

**New here?** → [Getting started](docs/GETTING-STARTED.md) · [SCUBA Ideaverse](docs/SCUBA-IDEAVERSE.md) · [Tour vault](examples/minimal-vault/) · [Team collaboration](docs/TEAM-COLLABORATION.md)

---

## How it's organized

```
build-research-wiki/
├── manager/              # SCUBA Ideaverse UI (FastAPI + React)
├── CLAUDE.md             # wiki schema — how the assistant operates
├── index.md, log.md      # catalog + chronological record
├── raw/                  # immutable uploads (dock here)
│   ├── papers/           #   portfolio PDFs
│   ├── literature/       #   lit review
│   ├── transcripts/      #   lab memory
│   └── notes/inbox/      #   ideas
├── builder/
│   ├── templates/        #   default entry templates per channel
│   ├── entries/          #   your chart notes (themes, abstract, one-liner)
│   ├── deepdives/        #   generative sections (RQ, method, findings, …)
│   ├── data.py           #   corpus (themes, papers, concepts, people)
│   └── build.py          #   chart generator
└── wiki/                 # generated chart (papers, themes, sources, …)
```

**Rule:** `raw/` is never modified by the chart build. Edit `builder/entries/` and `builder/deepdives/`, then re-run Surface Interval or `build.py`.

---

## Documentation

| Doc | What it covers |
|-----|----------------|
| [SCUBA Ideaverse](docs/SCUBA-IDEAVERSE.md) | UI workflow, channels, completion states, roadmap |
| [Getting started](docs/GETTING-STARTED.md) | Onboarding paths + first-session checklist |
| [Team collaboration](docs/TEAM-COLLABORATION.md) | Shared repos, git norms, privacy |
| [Changelog](docs/CHANGELOG.md) | Release notes (v0.3.0) |
| [Tour vault](examples/minimal-vault/) | Demo with 3 papers on chart |
| [CLAUDE.md](CLAUDE.md) | Full wiki schema |
| [BUILD.md](BUILD.md) | Deterministic builder |
| [manager/README.md](manager/README.md) | API reference |

---

## Requirements

| Tool | Purpose |
|------|---------|
| Python 3.7+ | Builder + SCUBA backend |
| Node 18+ | SCUBA frontend |
| [Obsidian](https://obsidian.md) | Browse the wiki (recommended) |
| LLM coding agent | Ingest, query, deep dives (Cursor, Claude Code, …) |
| [poppler](https://poppler.freedesktop.org/) | Optional — PDF title extraction |

---

## Credits

Implements the **[LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)** pattern. This template adds research-specific formats, a portfolio builder, SCUBA Ideaverse, and team docs.

## License

[MIT](LICENSE).
