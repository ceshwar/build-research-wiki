# Changelog

## v0.4.1 — Dock workspace & Map concepts (2026-06-20)

### Added

- **Dock workspace rail** — sticky **Chart status · Map · Actions** tabs scoped to the active dock
- **Map concepts column** — concept chips + synthesis links from `wiki/`; PDF moved into paper row
- **Per-reef onboarding guide** — dismissible hint resets when you switch reefs
- **First dock visit** — auto-expands Chart status the first time you open each dock on a reef

### Changed

- **Dive Computer** renamed to **Chart status** in the UI
- **Portfolio map** renamed to **Map** (dock-scoped)
- `GET /chart-map` returns `concepts` and `syntheses` per entry

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
