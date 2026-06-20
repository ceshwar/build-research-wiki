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

Open **http://127.0.0.1:5173** → pick **Shallow reef** in the header.

Requirements: **Python 3.7+**, **Node 18+**, optional **poppler** (`brew install poppler`) for PDF title extraction.

---

## Reefs (vaults)

| Reef | Path | Purpose |
|------|------|---------|
| **Shallow reef** | `examples/minimal-vault` | Low-stakes trial reef — 7 demo papers (3 deep dive, 4 enrich next). Learn the UI here. |
| **Blank reef** | repo root (`.`) | Empty scaffold — copy or run `new_vault.py` to spawn your lab reef. |
| **Your reefs** | local paths | Register via **+ Connect your reef…** (saved in `manager/backend/config/vaults.user.yaml`, gitignored). |

Built-in reefs ship in `manager/backend/config/vaults.yaml`. User-added reefs show under **Your reefs** in the dropdown.

---

## Workflow

```
Dock (raw/)  →  Quick Dip (Update chart)  →  Chart (wiki/)  →  Obsidian
                      │
         ┌────────────┴────────────┐
         │                         │
   Tier 1: PDF facts only    Tier 2+: Deep Dive
   (no guessing)             (themes, analysis, LLM agent)
```

1. **Pick a reef** — Shallow reef for demo, Blank reef or your own for real work.
2. **Pick a dock** — ⚓ My Portfolio, 🌊 Literature Review, … (first visit opens **Chart status**).
3. **Dock** — expand upload, drop files, **Confirm Upload** → `raw/{channel}/`
4. **Quick Dip** — runs automatically for portfolio uploads; or click **Update chart** in Actions
5. **Chart status** — pipeline stats and next-step banner for this dock
6. **Map** — browse charted items (List or By theme); concepts and syntheses from LLM ingest
7. **Deep Dive** — **Get ingest prompt** for your coding agent, or edit entries by hand
8. **Open reef in Obsidian** (header icon or map links)

Full chart spec: [`docs/PAPER-CHART-SPEC.md`](PAPER-CHART-SPEC.md)

---

## UI layout

| Area | What it does |
|------|----------------|
| **Header** | Reef dropdown (Starter reefs / Your reefs / Connect), Obsidian link, **Docs**, burger menu |
| **Docks** | Dock pills + collapsible upload |
| **Dock workspace rail** | **Map** first, then **Chart & enrich** (Chart status + Actions) — scrolls with the page |
| **Chart status** | Pipeline legend, clickable stat cards, next-step banner |
| **Map** | List \| By theme; paper row links PDF; **Concepts** column shows ingest output |
| **Actions** | **Update chart**, **Get ingest prompt** |

Open **Docs** for in-app glossary (reefs, SCUBA terms, pipeline states).

### Dock workspace (focus + discoverability)

When you select a dock, everything below the dock pills scopes to that channel:

- **Rail** — shows `⚓ My Portfolio · 7 on chart` and tabs. **Map** is primary; **Chart status** and **Actions** are grouped under **Chart & enrich**. Click a tab to jump; scroll updates the active tab.
- **Collapsible sections** — collapse Map or Actions if you only need Chart status.
- **Per-reef guide** — a one-line explainer appears until you dismiss it (**Got it**); it resets when you switch to a different reef.
- **First dock visit** — the first time you open a dock on a reef, **Map** expands automatically.

---

## Reef channels (docks)

Each reef has `builder/docks.yaml` — four built-in docks plus any you add in the UI:

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
| Deep dives | `builder/deepdives/<slug>.md` | you or LLM agent |
| Concepts / syntheses | `wiki/concepts/`, `wiki/syntheses/` | LLM ingest or hand-written |
| Auto registry | `builder/auto_papers.json`, `auto_sources.json` | generated — don't hand-edit |
| Chart pages | `wiki/papers/`, `wiki/sources/`, … | generated — don't hand-edit |

**Paper page shape** matches a fleshed-out portfolio entry — see `examples/minimal-vault/wiki/papers/positive-reinforcement-reddit.md`: frontmatter → one-liner → themes → abstract → deep dive → source links.

---

## Map columns

| Column | Source |
|--------|--------|
| **Status** | Quick dip / Deep dive / Enrich next |
| **Paper** | Wiki page link; **Note** expands one-liner + **View PDF** |
| **Themes** | `builder/entries/` wikilinks + `data.py` |

---

## Completion states (Chart status)

| Status | Meaning | What to do |
|--------|---------|------------|
| **Awaiting chart** | File in `raw/` but not on chart | Run **Update chart** |
| **Quick dip** | Tier 1 — PDF title/abstract/venue/year on chart | Deep Dive: add themes, one-liner, analysis |
| **Enrich next** | On chart but themes/deep dive incomplete | **Get ingest prompt** or edit entries + deepdives |
| **On chart** (deep dive done) | Fully enriched paper page | Refine in Obsidian if needed |

Portfolio uploads trigger Quick Dip automatically after **Confirm Upload**. Stat cards filter the Map.

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

# Agent batch prompt (same as UI "Get ingest prompt")
python3 builder/ingest_prompt.py --vault examples/minimal-vault --channel my-portfolio
```

---

## Connect your reef (UI — no YAML editing)

1. Click **+ Connect your reef…** in the header dropdown.
2. **Browse…** to pick your Obsidian vault folder (macOS/Linux native picker), or paste the path.
3. **Check folder** — confirms `builder/data.py`, paper count, etc.
4. **Connect** — saved locally in `manager/backend/config/vaults.user.yaml` (gitignored).

User-added reefs appear under **Your reefs**. **Remove from list** only unregisters the path — it does not delete your wiki.

Built-in reefs (**Shallow reef**, **Blank reef**) come from `vaults.yaml` in the repo.

### Configure built-in reefs (advanced)

To ship default reefs with the repo, edit `manager/backend/config/vaults.yaml`.

---

## What's next (roadmap)

Full issue list: **[docs/ROADMAP.md](ROADMAP.md)** · create on GitHub: `./scripts/create-roadmap-issues.sh`

| Phase | Feature |
|-------|---------|
| **Now (v0.4)** | Dock workspace, Map with concepts, Chart status, ingest prompt |
| **Phase 2** | LLM Deep Dive — auto-fill `builder/deepdives/` from PDFs |
| **Phase 2** | Theme/one-liner assistance, Enrich actions, entity propagation |
| **Phase 3** | Full LLM ingest for lit-review / dive-log / ideas (replaces preview shells) |
| **Phase 4** | Sonar ping (related work), query-to-file syntheses, overview threads |
| **Phase 5** | Reef profiles, Obsidian Dataview stats |

---

## See also

- [Getting started](GETTING-STARTED.md) — onboarding paths
- [Team collaboration](TEAM-COLLABORATION.md) — git norms, privacy
- [Shallow reef (demo)](../examples/minimal-vault/) — trial reef with 7 papers
- [manager/README.md](../manager/README.md) — API reference
- [builder/README.md](../builder/README.md) — builder internals
