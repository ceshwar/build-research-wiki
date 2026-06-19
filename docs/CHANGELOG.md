# Changelog

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
- **Tour vault** — `examples/minimal-vault/` with 5 papers on chart
- **Docs** — Getting started, team collaboration, SCUBA guide

### Changed

- Auto-mapping writes to `builder/entries/` instead of `raw/notes/abstracts/`
- Paper pages follow fleshed-out portfolio shape (abstract + structured deep dive)
- `CLAUDE.md` §10 updated for new chart-entry workflow

### Next

- LLM Deep Dive integration (fill deep dive sections from PDFs)
- Full LLM ingest for non-portfolio channels
- Related-work discovery (sonar ping)
