# Roadmap

Tracked as GitHub issues. To create them on a fresh clone:

```bash
gh auth login   # once
./scripts/create-roadmap-issues.sh
```

Issue bodies live in `scripts/roadmap-issues/*.md`. The script is safe to re-run — it skips titles that already exist.

## Shipped — v0.4 Ideaverse UI (2026-06-20)

Tracked in GitHub issue **#13 — v0.4 Ideaverse control panel — shipped** (closed).

| Area | Shipped |
|------|---------|
| **Workspace** | Focused shell: `/ Reef › Dock` path, Map · Chart status · Actions tabs |
| **Navigation** | Reef picker on `/`; dock picker on reef name; slim header (Docs + Obsidian) |
| **Map** | List + By theme; status filters; sortable columns; expandable Note + PDF |
| **Map edit** | Staged removals: Edit → mark − → Done confirms / Cancel discards |
| **Chart pipeline** | Quick Dip auto after upload; `off_chart.json` + remove-from-chart; batch API |
| **Chart status** | Per-dock stats; stat cards filter Map; Scaffolded / Enrich next / Quick dip pills |
| **Reefs** | Shallow reef (6-paper demo), Blank reef, Connect your reef, local sandbox copy |
| **Agent ingest** | Get ingest prompt (Actions tab) — manual Deep Dive workflow |
| **Builder** | `app/deps.py` shared VaultManager; 50 tests green on demo counts |

**Still open (Phase 2+):** LLM Deep Dive automation, theme assistance, per-paper Enrich buttons, full ingest docks, Sonar ping, query-to-file, **in-app viewer** (#14). See issues #1–#12, #14.

## Phases

| Phase | Focus | Issues |
|-------|--------|--------|
| **2** | Finish portfolio chart pipeline | LLM Deep Dive, theme assistance, Enrich actions, entity propagation |
| **3** | Full ingest for non-portfolio docks | Literature Review, Dive Log, Ideas & Notes |
| **4** | Discovery & synthesis | Sonar ping, query-to-file, overview threads |
| **5** | Product polish | Reef profiles, Obsidian Dataview stats |

## Non-portfolio docks today

| Dock | Upload | Update chart |
|------|--------|--------------|
| ⚓ My Portfolio | ✅ → `raw/papers/` | ✅ Full Quick Dip → `wiki/papers/` (auto after upload) |
| 🌊 Literature Review | ✅ → `raw/literature/` | ⚠️ Preview — thin `wiki/sources/` shell only |
| 🤿 Dive Log | ✅ → `raw/dive-log/` | ⚠️ Preview — shell only |
| 💡 Ideas & Notes | ✅ → `raw/notes/inbox/` | ⚠️ Preview — shell only |

Upload always works. **Update chart** on ingest docks shows an in-development callout and confirmation dialog; Phase 3 replaces preview with full LLM ingest per `CLAUDE.md` §6 INGEST.

See also: [SCUBA Ideaverse](SCUBA-IDEAVERSE.md) · [Paper chart spec](PAPER-CHART-SPEC.md)
