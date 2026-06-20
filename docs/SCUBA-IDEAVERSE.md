# SCUBA Ideaverse

**Your research world, mapped and connected.**

SCUBA Ideaverse is the control panel for this repo: dock research artifacts, surface structured charts, and open the result in Obsidian. It sits alongside the LLM-driven ingest workflow in [`CLAUDE.md`](../CLAUDE.md) — uploads stay in `raw/`; the chart build never modifies them.

---

## Quick start (team)

```bash
git clone https://github.com/ceshwar/build-research-wiki.git
cd build-research-wiki
./manager/scripts/dev.sh
```

Open **http://127.0.0.1:5173**

Requirements: **Python 3.7+**, **Node 18+**, optional **poppler** (`brew install poppler`) for PDF title extraction.

---

## Workflow

```
Dock (raw/)  →  Quick Dip (Update chart)  →  Chart (wiki/)  →  Obsidian
                      │
         ┌────────────┴────────────┐
         │                         │
   Tier 1: PDF facts only    Tier 2+: Deep Dive
   (no guessing)             (themes, analysis, LLM)
```

1. **Pick a channel** on the Dive Computer (My Portfolio, Lit Review, Lab Memory, …)
2. **Dock** — drop files, **Confirm Upload** → `raw/{channel}/`
3. **Quick Dip** — runs automatically for portfolio uploads; or click **Update chart (Quick Dip)** — maps artifacts → Tier 1 entries → rebuilds `wiki/`
4. **Deep Dive** — edit `builder/entries/` (themes, one-liner) and `builder/deepdives/` (analysis)
5. **Re-surface** when ready; check Dive Computer for completion counts
6. **Open reef in Obsidian**

Full chart spec: [`docs/PAPER-CHART-SPEC.md`](PAPER-CHART-SPEC.md)

---

## Reef channels (docks)

Each vault has `builder/docks.yaml` — four built-in docks plus any you add in the UI:

| Dock | Folder | Purpose | Chart today |
|------|--------|---------|-------------|
| ⚓ My Portfolio | `raw/papers/` | Your papers → Quick Dip chart | **Full** — auto after upload |
| 🌊 Literature Review | `raw/literature/` | Field papers to read | **Preview** — shell only (Phase 3) |
| 🤿 Dive Log | `raw/dive-log/` | Transcripts, session notes | **Preview** — shell only (Phase 3) |
| 💡 Ideas & Notes | `raw/notes/inbox/` | Quick captures | **Preview** — shell only (Phase 3) |

**+ Add dock** creates a new `raw/<slug>/` folder and registers it in `builder/docks.yaml`.

Non-portfolio docks: **upload works**; files stay in `raw/`. The UI shows an **in development** notice and asks for confirmation before **Update chart (preview)** — that path creates a thin `wiki/sources/` placeholder, not a finished ingest. Full LLM ingest is [Phase 3 on the roadmap](ROADMAP.md).

---

## Chart layers (what lives where)

| Layer | Path | Who edits |
|-------|------|-----------|
| Uploads (immutable) | `raw/papers/`, `raw/literature/`, … | you — dock only |
| Entry templates | `builder/templates/<channel>/` | copy to start by hand |
| Chart entries | `builder/entries/<channel>/<slug>.md` | you — themes, abstract, one-liner |
| Deep dives | `builder/deepdives/<slug>.md` | you or LLM (Phase 3) |
| Auto registry | `builder/auto_papers.json`, `auto_sources.json` | generated — don't hand-edit |
| Chart pages | `wiki/papers/`, `wiki/sources/`, … | generated — don't hand-edit |

**Paper page shape** matches a fleshed-out portfolio entry (see `examples/minimal-vault/wiki/papers/` or your personal `beyond-throughput` example): frontmatter → one-liner → themes → abstract → deep dive → source links.

---

## Completion states (Dive Computer)

| Status | Meaning | What to do |
|--------|---------|------------|
| **Pending** | File in `raw/` but not on chart | Run Update chart (Quick Dip) |
| **Quick dip** | Tier 1 — PDF title/abstract/venue/year on chart | Deep Dive: add themes, one-liner, analysis |
| **Needs deep dive** | Themes + abstract + one-liner filled; deep dive empty | Edit `builder/deepdives/<slug>.md` |
| **Deep dive done** | Fully enriched paper page | Refine in Obsidian if needed |

Portfolio uploads trigger Quick Dip automatically after **Confirm Upload**. The UI shows vault totals (**Quick dip**, **Deep dive done**, **Needs deep dive**, **Pending**) and per-channel breakdowns.

See [`docs/PAPER-CHART-SPEC.md`](PAPER-CHART-SPEC.md) for field-level rules (no guessing on Tier 1).

---

## CLI (without the UI)

```bash
# Quick Dip: map docked PDFs → builder/entries/ + auto registry
python3 builder/map_channel.py --channel my-portfolio
python3 builder/map_channel.py --vault examples/minimal-vault --channel lit-review

# QA Tier 1 (no guessing)
python3 builder/qa_quick_dip.py

# Rebuild chart
python3 builder/build.py
python3 builder/build.py --vault examples/minimal-vault --incremental
```

---

## Add a reef (UI — no YAML editing)

1. Click **+ Add reef** in the header.
2. **Browse…** to pick your Obsidian vault folder (macOS/Linux native picker), or paste the path.
3. **Check folder** — confirms `builder/data.py`, paper count, etc.
4. **Add reef** — saved locally in `manager/backend/config/vaults.user.yaml` (gitignored).

User-added reefs show a ★ in the dropdown. **Remove from list** only unregisters the path — it does not delete your wiki.

Built-in reefs (`demo`, `template`) still come from `vaults.yaml` in the repo.

### Configure vaults (advanced)

To ship default vaults with the repo, edit `manager/backend/config/vaults.yaml`:

---

## What's next (roadmap)

Full issue list: **[docs/ROADMAP.md](ROADMAP.md)** · create on GitHub: `./scripts/create-roadmap-issues.sh`

| Phase | Feature |
|-------|---------|
| **Now (v0.3+)** | Dock, Quick Dip (Tier 1), Deep Dive tracking, completion stats |
| **Phase 2** | LLM Deep Dive — auto-fill `builder/deepdives/` from PDFs |
| **Phase 2** | Theme/one-liner assistance, Enrich actions, entity propagation |
| **Phase 3** | Full LLM ingest for lit-review / dive-log / ideas (replaces preview shells) |
| **Phase 4** | Sonar ping (related work), query-to-file syntheses, overview threads |
| **Phase 5** | Reef profiles, Obsidian Dataview stats |

---

## See also

- [Getting started](GETTING-STARTED.md) — onboarding paths
- [Team collaboration](TEAM-COLLABORATION.md) — git norms, privacy
- [manager/README.md](../manager/README.md) — API reference
- [builder/README.md](../builder/README.md) — builder internals
