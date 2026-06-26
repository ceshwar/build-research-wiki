# Portolan

**Read what you dock. Chart the connections.**

Built for reading, in a world built for writing — Portolan keeps you oriented as the ocean of research keeps rising. The research assistant that actually reads your papers.

**Why "Portolan"?** A portolan is a navigational chart — a sailor's map of coastlines and harbors, drawn to keep you oriented at sea. This one keeps you oriented in *your field*, charting the papers you read and how they connect.

In a world that rewards writing and creating, almost nothing helps you read and connect. Portolan is a consumption tool. It reads what you dock and keeps you oriented in your field so you stop losing the thread.

Portolan is the layer between Zotero and Obsidian. Zotero stores, Obsidian links, neither reads your papers for you. The verb that is ours is **reads**. The asset is a compounding knowledge base: accumulation, not storage. Plain markdown you own and version with git. Works for one dissertation or a whole lab.

Built by the [SCUBA Lab](https://eshwarchandrasekharan.com/lab.html) at UIUC and shared openly under [MIT](LICENSE). Implements the [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) by Andrej Karpathy. The system (**dock → chart → enrich → Obsidian**) is corpus-agnostic: point it at your own papers and notes.

<p align="center">
  <img src="docs/images/portolan-hero.png" alt="Portolan — Shallow reef, My Portfolio, Navigate Graph with trust-tier filters" width="900">
</p>
<p align="center"><em>Shallow reef · My Portfolio — Navigate · Graph (Uncharted · Quick dip · Deep dive).</em></p>

---

## Why Portolan

| | Zotero / folders | Obsidian | ChatGPT / NotebookLM | Portolan |
|--|------------------|----------|----------------------|----------|
| **Job** | Store | Link | Answer in a session | Read and connect |
| **Persists** | Files | Your vault | Forgets when the tab closes | Compounding chart in git |
| **Inspectable** | Yes | Yes | Opaque | Plain markdown + sources |

Differentiator: persistent, inspectable, version-controlled, yours, and it compounds.

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
| **Shallow reef** | `examples/minimal-vault` | Low-stakes trial reef — 6 demo papers (3 deep dive, 3 quick dip). Learn the UI here. |
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
   Tier 1: PDF facts only    Tier 2: Deep Dive (LLM qwen3:32b)
   (no guessing)             → human review → charted territory
```

1. **Pick a reef** — Shallow reef for demo, Blank reef or your own for real work.
2. **Pick a dock** — hover dock pills for what each channel is for; first dock auto-opens **Navigate**.
3. **Workspace** — path header shows `Reef › Dock`; tabs: **Navigate**, **Query**, **Status**, **Actions**
4. **Dock** — click the dock name in the path to switch docks or upload → `raw/{channel}/`
5. **Quick Dip** — runs automatically for portfolio uploads; or click **Update chart** in Actions
6. **Status** — pipeline stats and next-step banner for this dock
7. **Navigate** — browse charted items (**List** table, **By theme**, or **Graph** on portfolio reefs); expand **Note** for one-liner + PDF
8. **Deep Dive** — **Run Deep Dive (LLM)** in Actions (default qwen3:32b), or **Get ingest prompt** for your agent
9. **Query** — ask questions against the wiki; cites [[sources]]; surfaces uncharted papers
10. **Settings** (⚙) — Ollama URL, models, local vs frontier provider, in-app vs Obsidian viewer
11. **Open in Obsidian** — optional; header icon or drawer link when viewing in-app

Full chart spec: [`docs/PAPER-CHART-SPEC.md`](PAPER-CHART-SPEC.md)

---

## UI layout

| Area | What it does |
|------|----------------|
| **Header** | **Settings** (⚙), **Docs**, **Open in Obsidian** |
| **Path bar** | `/` switches reefs · reef name picks dock · dock name is current location |
| **Reef picker** | Starter reefs, your reefs, **+ Connect your reef…** |
| **Workspace shell** | `Reef › Dock` path + tabs; Navigate / Query / Status / Actions |
| **Query** | Ask the wiki; LLM reads index + relevant pages; async job |
| **Actions** | **Update chart**, **Run Deep Dive (LLM)**, **Get ingest prompt**, upload |

Open **Docs** for in-app glossary (reefs, key terms, pipeline states).

### Focused dock workspace

When a reef and dock are selected, you work inside one card:

- **Path** — `/ Shallow reef › ⚓ My Portfolio`. Click **/** to switch reefs; click the reef name to choose a dock.
- **Tabs** — **Navigate** (default), **Status**, **Actions**. Hover a tab for a short hint. Only the active tab's content is shown.
- **Per-reef guide** — one-line explainer until dismissed (**Got it**); resets when you switch reefs.

Guide copy: **Navigate** browses your chart · **Status** tracks pipeline progress · **Actions** uploads, updates the chart, and runs Deep Dive.

---

## Navigate views

| View | When | What it shows |
|------|------|----------------|
| **List** | Always (portfolio + ingest docks) | Sortable table; **Edit** → mark **−** → **Done** / **Cancel** to remove from chart |
| **By theme** | Portfolio reefs only | Papers grouped by research theme (read-only) |
| **Graph** | Portfolio reefs only | Wikilink network from charted papers; click a node to open in Obsidian |

Status chips in Navigate: **All**, **Deep dive**, **Quick dip**. **Status** stat cards also filter Navigate when clicked (e.g. **Enrich next** shows papers needing Deep Dive).

### Graph edges

The graph seeds from charted papers and follows `[[wikilinks]]` in wiki pages. Typical edges:

- **paper → theme** (from chart data and page links)
- **paper → concept** (from deep dives and cross-links)
- **theme → theme**, **theme → paper** (when theme pages link to each other or back to papers)

Concept→concept links appear only if your concept pages link to each other. Toggle **Show** layers to include entities, syntheses, and sources.

**Edit mode** (List view only): click **Edit**, mark rows with **−**, then **Done** to confirm removals (or **Cancel** to discard). PDFs stay in `raw/` until **Update chart** maps them again.

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

## Completion states (Status)

| Status | Meaning | What to do |
|--------|---------|------------|
| **Awaiting chart** | File in `raw/` but not on chart | Run **Update chart** |
| **Quick dip** | Tier 1 — PDF title/abstract/venue/year on chart | Deep Dive: add themes, one-liner, analysis |
| **Scaffolded** | On chart from `data.py` but entry lacks themes, abstract, and one-liner | Edit `builder/entries/` or run Deep Dive |
| **Enrich next** | Themes/abstract present but deep dive incomplete | **Get ingest prompt** or edit `builder/deepdives/` |
| **On chart** (deep dive done) | Fully enriched paper page | Refine in Obsidian if needed |

Portfolio uploads trigger Quick Dip automatically after **Confirm Upload**. Stat cards filter Navigate.

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

---

## What's next (roadmap)

Full issue list: **[docs/ROADMAP.md](ROADMAP.md)** · create on GitHub: `./scripts/create-roadmap-issues.sh`

| Phase | Feature |
|-------|---------|
| **Now (v0.6)** | LLM Deep Dive in-app, Query tab, Settings, in-app viewer, verification/territory |
| **Phase 2** | Theme/one-liner assistance, per-paper Deep Dive button, entity propagation |
| **Phase 3** | Full LLM ingest for lit-review / dive-log / ideas (replaces preview shells) |
| **Phase 4** | Sonar ping (related work), query-to-file syntheses, overview threads |
| **Phase 5** | Reef profiles, Obsidian Dataview stats |

---

## See also

- [Getting started](GETTING-STARTED.md) — onboarding paths
- [Team collaboration](TEAM-COLLABORATION.md) — git norms, privacy
- [Shallow reef (demo)](../examples/minimal-vault/) — trial reef with 6 papers
- [manager/README.md](../manager/README.md) — API reference
- [builder/README.md](../builder/README.md) — builder internals
