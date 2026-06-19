# Roadmap

Tracked as GitHub issues. To create them on a fresh clone:

```bash
gh auth login   # once
./scripts/create-roadmap-issues.sh
```

Issue bodies live in `scripts/roadmap-issues/*.md`. The script is safe to re-run — it skips titles that already exist.

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
