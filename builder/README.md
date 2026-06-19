# builder/ — the LLM-Wiki generator

All code that generates this vault lives here. It's **portable** (auto-detects the vault it
sits in), **idempotent** (re-run anytime), and **data-driven** (swap `data.py` for a new corpus).

## Run it
```bash
python3 builder/build.py            # rebuild this vault's papers/themes/concepts/entities + index.md
```
Output ends with a link check (`red links: NONE` = healthy). Requires Python 3 only.
PDF text extraction (optional, below) needs **poppler** (`brew install poppler`).

## Files
| File | Role | Edit per vault? |
|---|---|---|
| `build.py` | Entrypoint — runs both engines + link check; finds the vault as its parent | no |
| `engine_papers.py` | Generic engine → `wiki/papers/`, `wiki/themes/`, `index.md` | no |
| `engine_web.py` | Generic engine → `wiki/concepts/`, `wiki/entities/` | no |
| **`data.py`** | **The corpus**: THEMES, P (papers), TITLES, CONCEPTS, PEOPLE, PLATFORMS, METHODS | **yes** |
| `deepdives/<slug>.md` | **Source of truth** for each paper's *Deep dive* section (injected at build) | yes (content) |
| `extract_pdfs.py` | Helper: `pdftotext` every paper PDF → `cache/<slug>.txt` (for writing deep dives) | no |
| `new_vault.py` | Scaffold a brand-new vault that reuses this engine | no |
| `cache/` | Disposable extracted PDF text (gitignored) | — |

## Two rules
1. **Deep dives:** edit `builder/deepdives/<slug>.md`, then re-run. Editing the *Deep dive*
   block inside `wiki/papers/<slug>.md` directly will be overwritten.
2. **Hand-maintained (never generated):** `wiki/overview.md`, `wiki/syntheses/`, `log.md`,
   `CLAUDE.md`, root `BUILD.md`.

## Add a paper
1. Abstract note → `raw/notes/recent project abstracts/(YEAR_VENUE) Title.md` (`[[Theme]]` on
   line 1, then `## Abstract:`). PDF → `raw/papers/`.
2. Add a row to `P` in `data.py`. (Optional: add concept/entity/title entries.)
3. `python3 builder/extract_pdfs.py` then write `builder/deepdives/<slug>.md`.
4. `python3 builder/build.py`. Update `wiki/overview.md` + `log.md` by hand.

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
