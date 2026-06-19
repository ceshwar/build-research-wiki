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
Dock (raw/)  →  Surface Interval  →  Chart (wiki/)  →  Obsidian
                      │
         ┌────────────┴────────────┐
         │                         │
   Deterministic scaffold    LLM Deep Dive (next)
   (templates → entries)     (generative sections)
```

1. **Pick a channel** on the Dive Computer (My Portfolio, Lit Review, Lab Memory, …)
2. **Dock** — drop files, **Confirm Upload** → `raw/{channel}/`
3. **Surface Interval** — map artifacts → scaffold chart entries → rebuild `wiki/`
4. **Edit entries** — fill themes, abstract, one-liner in `builder/entries/`; deep dive in `builder/deepdives/`
5. **Re-surface** when ready; check Dive Computer for completion counts
6. **Open reef in Obsidian**

---

## Reef channels

| Channel | Upload path | Chart output |
|---------|-------------|--------------|
| My Portfolio | `raw/papers/` | `wiki/papers/`, themes, concepts |
| Lab Portfolio | `raw/lab/papers/` | same (lab corpus) |
| Literature Review | `raw/literature/` | `wiki/sources/` shells |
| Lab Memory | `raw/transcripts/` | `wiki/sources/` shells |
| Ideas & Notes | `raw/notes/inbox/` | `wiki/sources/` shells |

---

## Chart layers (what lives where)

| Layer | Path | Who edits |
|-------|------|-----------|
| Uploads (immutable) | `raw/papers/`, `raw/literature/`, … | you — dock only |
| Entry templates | `builder/templates/<channel>/` | copy to start by hand |
| Chart entries | `builder/entries/<channel>/<slug>.md` | you — themes, abstract, one-liner |
| Deep dives | `builder/deepdives/<slug>.md` | you or LLM (Phase 3) |
| Auto registry | `builder/auto_papers.py`, `auto_sources.py` | generated — don't hand-edit |
| Chart pages | `wiki/papers/`, `wiki/sources/`, … | generated — don't hand-edit |

**Paper page shape** matches a fleshed-out portfolio entry (see `examples/minimal-vault/wiki/papers/` or your personal `beyond-throughput` example): frontmatter → one-liner → themes → abstract → deep dive → source links.

---

## Completion states (Dive Computer)

| Status | Meaning | What to do |
|--------|---------|------------|
| **Pending surface** | File in `raw/` but not mapped | Run Surface Interval |
| **Scaffolded** | On chart; themes/abstract/one-liner empty | Edit `builder/entries/<channel>/<slug>.md` |
| **Charted** | Deterministic parts filled; deep dive empty | Edit `builder/deepdives/<slug>.md` |
| **Processed** | Fully charted (like a finished paper page) | Nothing — or refine in Obsidian |

The UI shows vault totals (**Processed**, **Needs review**, **Pending surface**) and per-channel entry lists for items that need attention.

---

## CLI (without the UI)

```bash
# Map docked PDFs → builder/entries/ + auto registry
python3 builder/map_channel.py --channel my-portfolio
python3 builder/map_channel.py --vault examples/minimal-vault --channel lit-review

# Rebuild chart
python3 builder/build.py
python3 builder/build.py --vault examples/minimal-vault --incremental
```

---

## Configure vaults

Edit `manager/backend/config/vaults.yaml`:

```yaml
vaults:
  - id: demo
    name: Tour vault
    path: examples/minimal-vault
  - id: my-lab
    name: Our lab wiki
    path: /absolute/path/to/your/vault
```

---

## What's next (roadmap)

| Phase | Feature |
|-------|---------|
| **Now (v0.3)** | Dock, Surface Interval, template scaffolds, completion tracking |
| **Phase 3** | LLM Deep Dive — auto-fill `builder/deepdives/` from PDFs |
| **Phase 3** | LLM ingest for lit-review / lab-memory / ideas → full `wiki/sources/` |
| **Later** | Sonar ping (related work), reef profiles (custom chart shapes) |

---

## See also

- [Getting started](GETTING-STARTED.md) — onboarding paths
- [Team collaboration](TEAM-COLLABORATION.md) — git norms, privacy
- [manager/README.md](../manager/README.md) — API reference
- [builder/README.md](../builder/README.md) — builder internals
