# Changelog

## v0.5.0 — Portolan rebrand (2026-06-20)

### Changed

- **Product name** — SCUBA Ideaverse → **Portolan** (SCUBA Lab remains author/org)
- **Workspace tabs** — Map → **Navigate**, Chart status → **Status** (Actions unchanged)
- **Navigate render modes** — List · By theme · Graph (unchanged)
- **Positioning copy** — README, in-app Docs, `docs/PORTOLAN.md` (replaces `docs/SCUBA-IDEAVERSE.md` stub redirect)
- **Graph** — theme slug alias resolution (`algorithmic-and-ai-audits` → `algorithmic-ai-audits`); Docs explain edge types

### Unchanged

- Pipeline: dock → chart → enrich → Obsidian
- Nautical terms: reef, dock, Quick Dip, Deep Dive
- **Chart** as corpus noun and build verb

---

## v0.4.6 — Map Graph view (2026-06-20)

### Added

- **Graph tab** on portfolio dock Map — force-directed wikilink network (papers, themes, concepts, entities, syntheses) from `wiki/` files
- **`GET /chart-graph`** + `builder/chart_graph.py`; status filters and type legend; click node → Obsidian
- **Obsidian vault-ID links** — auto-detect registered vaults; optional `obsidian_vault_id` override for sandbox reefs

### Changed

- Map removal errors surface in UI; batch-delete fallback for older backends; backend `--reload` in `dev.sh`

### Docs / issues

- GitHub **#15** (graph shipped); **#14** (in-app viewer, follow-up)

---

## v0.4.5 — Staged map edits (2026-06-20)

### Changed

- **Map Edit flow** — **Edit** → mark rows with **−** → **Done** confirms batch removal (or **Cancel** discards); no per-click confirm
- **Done** shows count (`Done · remove 3`); marked rows tint red until applied or cancelled
- **Scaffolded** status pill on Map (portfolio rows from `data.py` still missing themes/abstract/one-liner)

### Added

- **Batch remove** — `POST /chart-remove` removes multiple slugs with one incremental rebuild

### Docs

- Scaffolded + Edit flow documented in `docs/SCUBA-IDEAVERSE.md`, in-app Docs, `docs/ROADMAP.md`

---

## v0.4.4 — Map edit mode & remove from chart (2026-06-20)

### Added

- **Map Edit mode** — toggle on List view to reveal **−** remove controls; off by default for clean demos
- **Remove from chart** — `DELETE /chart-entry` + `builder/remove_from_chart.py`; PDF stays in `raw/` as awaiting chart; `builder/off_chart.json` tracks removals until re-charted
- **Local demo reef** — copy portfolio to `examples/local-reef/` (gitignored) via user vault config; isolated from your live Obsidian vault

### Changed

- Remove controls use a red **−** button (sticky left column) visible only in Edit mode

### Docs

- README, `docs/SCUBA-IDEAVERSE.md`, `manager/README.md`, in-app Docs updated for Edit mode

---

## v0.4.3 — Path navigation & demo trim (2026-06-20)

### Changed

- **Header** slimmed to **Docs** + **Obsidian** only; reef picker moved to **`/`** in the workspace path
- **Path bar** — `/` switches reefs, reef name opens dock picker, dock name is the current location
- **Shallow reef** — removed unpublished Positive Queue paper (6 papers: 3 deep dive, 3 quick dip)
- README hero screenshot updated for focused workspace + Map view

---

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
- Demo reef expanded to **6 papers** (3 deep dive, 3 enrich next) for ingest-prompt walkthrough
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
