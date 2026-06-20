# Changelog

## v0.4.2 — Focused dock workspace (2026-06-20)

### Changed

- **Focused workspace** — once a reef and dock are selected, the UI shows a single panel: path header (`Reef › Dock`), tabs (**Map · Chart status · Actions**), and only the active tab’s content. Docks/upload open when you click the dock name in the path.
- **Map filters** — status chips trimmed to **All**, **Deep dive**, and **Quick dip** (Chart status stat cards still filter the map).
- **Dock picker** — descriptions removed from the panel; hover a dock pill for purpose + file counts.
- **Map** — expandable **Note** per paper (wiki one-liner + View PDF); sortable columns; no Concepts column.

### Added

- **Path breadcrumb** — `Reef › Dock` header in the workspace shell; workspace tab tooltips on hover.

### Docs

- Aligned `README.md`, `docs/SCUBA-IDEAVERSE.md`, `docs/GETTING-STARTED.md`, `manager/README.md`, and in-app **Docs** to the focused workspace layout.

---

## v0.4.1 — Dock workspace & Map notes (2026-06-20)

### Added

- **Dock workspace** — per-dock **Map · Chart status · Actions** tabs
- **Map Note column** — expandable one-liner + **View PDF** from wiki overview
- **Per-reef onboarding guide** — dismissible hint resets when you switch reefs

### Changed

- **Dive Computer** renamed to **Chart status** in the UI
- **Portfolio map** renamed to **Map** (dock-scoped)
- `GET /chart-map` returns `overview` per entry (replaces concepts column)

---

## v0.4.0 — Portfolio map & reef rebrand (2026-06-19)

### Added

- **Portfolio map** in SCUBA — List / By theme tabs, Obsidian links, stat-card filters
- **Get ingest prompt** — agent-ready batch prompt with allowed themes + full-PDF read instruction
- **In-app Docs** — SCUBA glossary (reefs, pipeline, completion states)
- **Shallow reef** / **Blank reef** built-in reefs; **+ Connect your reef…** for local vaults
- **`GET /chart-map`** API for portfolio map data

### Changed

- SCUBA UI refactor — workflow panel, collapsible upload, Dive Computer, burger nav
- Demo reef expanded to **7 papers** (3 deep dive, 4 enrich next) for ingest-prompt walkthrough
- Docs aligned to reef terminology and current UI workflow

---

## v0.3.0 — SCUBA Ideaverse (2026-06-19)

First shareable release of the research wiki manager.

### Added

- **SCUBA Ideaverse** — web UI (`manager/`) for docking artifacts and surfacing charts
- **Reef channels** — My Portfolio, Lab Portfolio, Lit Review, Lab Memory, Ideas
- **Dock → Surface Interval** workflow; uploads stay in `raw/` only
- **Template-driven chart entries** — `builder/templates/` → `builder/entries/<channel>/`
- **Deep dive scaffolds** — `builder/deepdives/<slug>.md` (generative sections for LLM/manual fill)
- **Completion tracking** — Dive Computer shows processed / needs review / pending counts
- **Incremental builds** — `builder/build.py --incremental` skips unchanged pages
- **Tour vault** — `examples/minimal-vault/` (superseded by **Shallow reef** in v0.4)
- **Docs** — Getting started, team collaboration, SCUBA guide

### Changed

- Auto-mapping writes to `builder/entries/` instead of `raw/notes/abstracts/`
- Paper pages follow fleshed-out portfolio shape (abstract + structured deep dive)
- `CLAUDE.md` §10 updated for new chart-entry workflow

### Next

- LLM Deep Dive integration (fill deep dive sections from PDFs)
- Full LLM ingest for non-portfolio channels
- Related-work discovery (sonar ping)
