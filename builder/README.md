# builder/ — the LLM-Wiki generator

All code that generates this vault lives here. It's **portable** (auto-detects the vault it
sits in), **idempotent** (re-run anytime), and **data-driven** (swap `data.py` for a new corpus).

## Run it
```bash
python3 builder/map_channel.py --channel my-portfolio   # docked PDFs → builder/entries/
python3 builder/build.py            # scaffold wiki chart from entries + data.py
```

## Chart layers

| Layer | Location | Who edits |
|-------|----------|-----------|
| Uploads (immutable) | `raw/papers/`, `raw/literature/`, … | you dock files |
| Deterministic entries | `builder/entries/<channel>/<slug>.md` | you (copy from `builder/templates/`) |
| Generative deep dives | `builder/deepdives/<slug>.md` | LLM Deep Dive later, or by hand |
| Chart output | `wiki/papers/`, `wiki/sources/`, … | generated — do not edit |

Output ends with a link check (`red links: NONE` = healthy). Requires Python 3 only.
PDF text extraction (optional, below) needs **poppler** (`brew install poppler`).

## Files
| File | Role | Edit per vault? |
|---|---|---|
| `build.py` | Entrypoint — runs engines + link check | no |
| `map_channel.py` | Docked artifacts → `builder/entries/` + auto registry | no |
| `engine_papers.py` | Portfolio chart → `wiki/papers/`, `wiki/themes/`, `index.md` | no |
| `engine_ingest.py` | Ingest channels → `wiki/sources/` shells | no |
| `engine_web.py` | Concepts + entities | no |
| `templates/` | Default entry templates per channel (copy to start by hand) | no |
| **`data.py`** | Corpus: THEMES, P, CONCEPTS, PEOPLE, … | **yes** |
| `entries/<channel>/` | Your working chart notes (deterministic sections) | **yes** |
| `deepdives/<slug>.md` | Generative *Deep dive* section (injected at build) | yes |
| `auto_papers.py` / `auto_sources.py` | Registry of auto-mapped dock artifacts | auto |
| `extract_pdfs.py` | `pdftotext` → `cache/<slug>.txt` | no |
| `new_vault.py` | Scaffold a new vault | no |
| `cache/` | Disposable PDF text (gitignored) | — |

## Two rules
1. **Entries:** edit `builder/entries/<channel>/<slug>.md`, then Surface Interval / `build.py`.
   Uploads in `raw/` are never modified by the chart build.
2. **Deep dives:** edit `builder/deepdives/<slug>.md` (or run LLM Deep Dive when available).
3. **Hand-maintained:** `wiki/overview.md`, `wiki/syntheses/`, `log.md`, `CLAUDE.md`.

## Add a paper
1. Dock PDF → `raw/papers/` (or copy `builder/templates/my-portfolio/entry.md` to
   `builder/entries/my-portfolio/<slug>.md` and fill in by hand).
2. `python3 builder/map_channel.py --channel my-portfolio` — creates entry from template if needed.
3. Add theme links and abstract in the **entry file** (not `raw/notes/`).
4. Register in `data.py` `P` if hand-curated; auto-mapped papers land in `auto_papers.py`.
5. `python3 builder/build.py`. Update `wiki/overview.md` + `log.md` by hand.

Legacy: hand-curated abstract notes in `raw/notes/abstracts/` still work if referenced from `data.py`.

## Clone for a different set of papers
```bash
python3 builder/new_vault.py ~/Desktop/Climate-Brain "Climate Brain"
```
Creates a fresh vault skeleton with a **copy of this engine** and a starter `data.py`. Then add
sources to its `raw/`, fill its `builder/data.py`, and run its `builder/build.py`. The engine
files are identical across vaults; only `data.py` + `raw/` + `deepdives/` differ.

## Scheduling (future)
`build.py` is a plain, idempotent CLI returning exit code 0 (healthy) / 1 (red links), so it
drops straight into cron / launchd / a CI job, e.g. nightly (replace the path with your vault's
current location — the builder itself is path-independent, so renaming/moving the vault is fine):
```
0 3 * * *  cd "/path/to/your-vault" && /usr/bin/python3 builder/build.py
```
