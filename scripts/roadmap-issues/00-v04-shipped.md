## Summary

v0.4.x delivers the **SCUBA Ideaverse control panel** — a local web UI for docking artifacts, Quick Dip charting, Map browsing, Chart status, and manual Deep Dive via ingest prompt. This issue is a **shipped checklist**; Phase 2–5 roadmap issues (#1–#12) remain open for automation and ingest expansion.

## Shipped

### Workspace & navigation
- [x] Focused dock workspace: ` / Reef › Dock` path + Map · Chart status · Actions tabs
- [x] Reef picker on `/`; dock picker on reef name; header = Docs + Obsidian only
- [x] Per-reef onboarding guide (localStorage dismiss)

### Map
- [x] List (sortable Status / Paper / Themes) + By theme (portfolio)
- [x] Status filters: All, Deep dive, Quick dip; Chart status stat cards filter map
- [x] Expandable **Note** (one-liner + View PDF)
- [x] **Edit mode** — mark rows with −, **Done** batch-confirms removal, **Cancel** discards
- [x] Status pills: Quick dip, Enrich next, Deep dive, **Scaffolded**

### Chart pipeline
- [x] Dock upload → `raw/`; Quick Dip auto after portfolio upload
- [x] Remove from chart (`builder/remove_from_chart.py`, `off_chart.json`)
- [x] `DELETE /chart-entry`, `POST /chart-remove` (batch)
- [x] Get ingest prompt (Actions) for manual agent Deep Dive

### Reefs & demo
- [x] Shallow reef — 6 papers (3 deep dive, 3 quick dip); Positive Queue removed
- [x] Blank reef + Connect your reef (`vaults.user.yaml`, gitignored)
- [x] Local sandbox copy pattern (`examples/local-reef/`, gitignored)

### Engineering
- [x] Shared `VaultManager` singleton (`app/deps.py`)
- [x] Test suite aligned to 6-paper demo (50 passed)

## Not in v0.4 (see open issues)

- LLM Deep Dive automation (#1)
- Theme / one-liner assistance (#2)
- Per-paper Enrich buttons in UI (#3)
- Full ingest for lit-review / dive-log / ideas (#5–#7)
- Sonar ping, query-to-file, overview threads (#8–#10)

## References

- `docs/CHANGELOG.md` (v0.4.3–v0.4.5)
- `docs/SCUBA-IDEAVERSE.md`
- `manager/README.md`
