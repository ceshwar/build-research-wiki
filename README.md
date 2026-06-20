# SCUBA Ideaverse

**Your research world, mapped and connected.**

An LLM-powered research wiki — a persistent, compounding knowledge base that an AI assistant
maintains for you. Dock papers and notes; browse the result in [Obsidian](https://obsidian.md).

Built by the [SCUBA Lab](https://eshwarchandrasekharan.com/lab.html) at UIUC and shared openly
under [MIT](LICENSE). We run it on our own research portfolio — but the system (**dock → chart →
enrich → Obsidian**) is corpus-agnostic, so any lab or researcher can point it at their own
papers and notes. Implements the
[LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) by Andrej
Karpathy — compile knowledge once and keep it current.

<p align="center">
  <img src="docs/images/scuba-main-ui.png" alt="SCUBA Ideaverse — docks, chart status, and map on Shallow reef" width="900">
</p>
<p align="center"><em>Shallow reef demo — pick a dock, track chart status, browse the map, then open in Obsidian.</em></p>

---

## The control panel (v0.4.2)

A web app for docking artifacts, **Quick Dip** (Tier 1 PDF facts on chart), **Deep Dive** enrichment, per-dock **Map** browsing, and **Chart status** tracking.

```bash
./manager/scripts/dev.sh    # → http://127.0.0.1:5173
```

| Step | Action |
|------|--------|
| 1 | Pick a **reef**, then a **dock** (hover pills for what each channel is) |
| 2 | Work in the **workspace** — `Reef › Dock` path, tabs for Map / Chart status / Actions |
| 3 | **Dock** files — click the dock name in the path, or **Upload PDFs** in Actions |
| 4 | Check **Chart status** — on chart, quick dip, enrich next |
| 5 | Browse the **Map** — List or By theme (portfolio); expand **Note** for one-liner + PDF |
| 6 | **Deep Dive** via **Get ingest prompt** or edit `builder/entries/` + `builder/deepdives/` |
| 7 | Open reef in Obsidian |

Full guide: **[docs/SCUBA-IDEAVERSE.md](docs/SCUBA-IDEAVERSE.md)** · Chart spec: **[docs/PAPER-CHART-SPEC.md](docs/PAPER-CHART-SPEC.md)**

---

## Three ways to use it

### 1. SCUBA Ideaverse (UI) — *recommended for teams*

Dock → Quick Dip → Deep Dive → Obsidian. Uploads stay in `raw/`; Tier 1 chart entries land in `builder/entries/` from PDF facts only (no guessing). **Chart status** shows **Quick dip**, **Enrich next**, and **On chart** counts per dock.

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

# Option A — try the UI + Shallow reef (demo)
./manager/scripts/dev.sh
# → http://127.0.0.1:5173 — pick **Shallow reef** in the header

# Option B — browse the demo reef in Obsidian
open examples/minimal-vault   # or: File → Open folder as vault in Obsidian

# Option C — start your own reef
python3 builder/new_vault.py ~/my-research-wiki "My Lab"
```

**New here?** → [Getting started](docs/GETTING-STARTED.md) · [SCUBA Ideaverse](docs/SCUBA-IDEAVERSE.md) · [Shallow reef (demo)](examples/minimal-vault/) · [Team collaboration](docs/TEAM-COLLABORATION.md)

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

**Rule:** `raw/` is never modified by the chart build. Edit `builder/entries/` and `builder/deepdives/`, then re-run **Update chart** in the UI or `build.py`.

---

## Documentation

| Doc | What it covers |
|-----|----------------|
| [SCUBA Ideaverse](docs/SCUBA-IDEAVERSE.md) | UI workflow, channels, completion states, roadmap |
| [Roadmap](docs/ROADMAP.md) | Phased next steps + GitHub issue script |
| [Getting started](docs/GETTING-STARTED.md) | Onboarding paths + first-session checklist |
| [Team collaboration](docs/TEAM-COLLABORATION.md) | Shared repos, git norms, privacy |
| [Changelog](docs/CHANGELOG.md) | Release notes (v0.4.1) |
| [Shallow reef (demo)](examples/minimal-vault/) | Trial reef — 7 papers (3 deep dive, 4 enrich next) |
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

Built by the **[SCUBA Lab](https://eshwarchandrasekharan.com/lab.html)** (Social Computing, User Behavior, and AI) at UIUC. Implements the **[LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)** pattern by Andrej Karpathy, adding research-specific formats, a portfolio chart builder, the SCUBA Ideaverse control panel, and team docs. Shared openly so other labs can run it on their own corpus.

## License

[MIT](LICENSE).
