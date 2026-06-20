# Log

Append-only, chronological record of every operation on this wiki. Newest entries at the
bottom. Each entry starts with `## [YYYY-MM-DD] <ingest|query|lint|synthesis> | <label>` so
`grep "^## \[" log.md | tail -5` shows recent history. See CLAUDE.md §7.

## [setup] Research Wiki scaffolded from the build-research-wiki template.

## [2026-06-19] release | v0.4 portfolio map, reef rebrand, docs sync
- SCUBA UI: portfolio map, Docs panel, Shallow reef / Blank reef / Connect your reef.
- Shallow reef demo: 7 papers (3 deep dive, 4 enrich next); ingest prompt walkthrough.
- Docs updated: README, GETTING-STARTED, SCUBA-IDEAVERSE, TEAM-COLLABORATION, CHANGELOG.

## [2026-06-19] docs | High-impact onboarding
- Added `docs/GETTING-STARTED.md`, `docs/TEAM-COLLABORATION.md`, `AGENTS.md`, Karpathy attribution in README.
- Added `examples/minimal-vault/` Shallow reef demo (7 papers; 3 UIUC deep dives + 4 Quick Dip).
