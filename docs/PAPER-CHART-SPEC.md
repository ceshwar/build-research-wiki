# Paper chart spec — Quick Dip vs Deep Dive

Chart entries are **product IP**: structured wiki pages we generate for users. Tier 1 must be factual and QA'd — no guessing, no placeholder text that looks like real content.

---

## Tiers

| Tier | Name | Trigger | What gets filled |
|------|------|---------|-------------------|
| **1** | **Quick Dip** | Dock + **Update chart** (auto after portfolio upload) | PDF-derived facts only |
| **2+** | **Deep Dive** | **Run Deep Dive (LLM)** in Actions, or agent/manual edit | Themes, one-liner, analysis, cross-links |

**Quick Dip** = a first pass on the chart. **Deep Dive** = enrichment to a finished paper page (see `examples/minimal-vault/wiki/papers/positive-reinforcement-reddit.md`).

---

## Quick Dip (Tier 1) — rules

### Source of truth

- Read from the artifact in `raw/` (usually PDF via `pdftotext`).
- **Never** modify `raw/`.
- **Never** invent metadata. If a field is not in the PDF (or filename for year only), leave it empty.

### Fields populated automatically

| Field | Source | If missing |
|-------|--------|------------|
| **Title** | First page of PDF | Empty — user/Deep Dive fills |
| **Abstract** | `Abstract` section in PDF | Empty `## Abstract` section |
| **Venue** | Pattern match on first pages (CHI, CSCW, ICWSM, arXiv, …) | `—` on wiki page |
| **Year** | Venue line, PDF text, or filename | `—` on wiki page |
| **Themes** | — | Not set (no `[[theme-slug]]` placeholders) |
| **One-liner** | — | Empty `## One-liner` |
| **Deep dive** | — | **Not created** — no `builder/deepdives/<slug>.md` scaffold |

### Forbidden in Quick Dip output

- `venue: unknown`
- `[[theme-slug]]` or similar template placeholders
- `Auto-mapped from PDF`, `Docked PDF`, `fill themes`, `Pending LLM` boilerplate in entry body
- Filename used as title when PDF text is unavailable
- Today's date as publication year

### Where it lands

```
raw/papers/foo.pdf                          # immutable upload
builder/entries/my-portfolio/foo.md         # Quick Dip entry (edit here)
builder/auto_papers.json                    # registry row (status: quick-dip)
wiki/papers/foo.md                          # generated chart page
```

Entry file header:

```markdown
<!-- chart-tier: quick-dip — PDF-derived fields only; Deep Dive to enrich -->

## Abstract
<text from PDF or empty>

## One-liner

## My notes
```

---

## Deep Dive (Tier 2+)

**In-app (v0.6):** Actions → **Run Deep Dive (LLM)** calls `builder/deep_dive_llm.py` via Ollama (default **qwen3:32b** on GPU tunnel `127.0.0.1:11500`). Writes `builder/entries/`, `builder/deepdives/`, marks `enrichment_source` and **needs human review**.

User, frontier model, or agent can also enrich manually:

1. **Themes** — `[[wikilinks]]` on line 1 of `builder/entries/<channel>/<slug>.md`
2. **One-liner** — `## One-liner` in entry file
3. **Deep dive** — `builder/deepdives/<slug>.md` (RQ, method, findings, limitations, …)
4. Optional: concept/entity pages, synthesis updates

Re-run **Update chart** after edits to refresh `wiki/`.

### Enrichment sources (stored in `builder/verification.json` + wiki frontmatter)

| `enrichment_source` | Meaning |
|---------------------|---------|
| `quick-dip` | Tier 1 PDF facts only |
| `local-32b` | LLM Deep Dive via local Ollama (e.g. qwen3:32b) |
| `local-custom` | LLM Deep Dive via another local model |
| `frontier` | LLM Deep Dive via Anthropic/OpenAI |
| `human` | Hand-charted / user-verified corpus |

### Territory

| `territory` | Meaning |
|-------------|---------|
| `charted` | You have read/verified (or hand-authored `status: mapped`) |
| `uncharted` | LLM-filled Deep Dive awaiting your review — surfaced in **Query** and **Needs review** filters |

Mark **verified** in Portolan after reading; wiki pages get `human_verified: true` and an Obsidian callout.

---

## Completion states (Chart status)

| State | Meaning |
|-------|---------|
| **Pending** | In `raw/` but not on chart |
| **Quick dip** | Tier 1 done — PDF facts on chart; themes/one-liner/deep dive still empty |
| **Needs deep dive** | Themes + abstract + one-liner filled; deep dive incomplete |
| **Deep dive done** | Fully enriched (processed) — may still **need review** if LLM-generated |
| **Needs review** | Processed but `human_verified: false` |
| **Uncharted** | LLM territory — read when Query surfaces it or from Status filter |

---

## UI flow

1. User docks a PDF to a **portfolio** channel → **Confirm upload**
2. **Quick Dip runs automatically** (same as **Update chart (Quick Dip)**)
3. Chart status shows **Quick dip** / **Enrich next** / **On chart** counts
4. User edits entries and deep dives in Obsidian or repo; re-surfaces when ready
5. **Edit mode** on the Map (List view) — **Edit** → mark **−** → **Done** confirms removals ( **Cancel** discards); PDF stays in `raw/` until **Update chart**

Ingest channels (lit-review, lab-memory, ideas) also get Quick Dip shells in `builder/entries/` → `wiki/sources/`; Deep Dive fills generative sections later.

---

## QA

```bash
python3 builder/qa_quick_dip.py
```

Checks:

- Real PDF extraction (title, abstract, venue, year)
- No forbidden placeholders in entry bodies
- `map_channel` pipeline: `status=quick-dip`, no `deepdives/` scaffold
- Legacy `inferred` entries refresh to Quick Dip on next Update chart

Requires **poppler** (`pdftotext`) for PDF tests.

---

## Implementation map

| Module | Role |
|--------|------|
| `builder/quick_dip.py` | PDF/text extraction + entry body builder |
| `builder/map_channel.py` | Map `raw/` → entries + auto registry; refresh stale rows |
| `builder/engine_papers.py` | Wiki paper pages; 🤿 icon for quick-dip |
| `builder/deep_dive_llm.py` | LLM Deep Dive (Ollama / frontier) |
| `builder/verification.py` | `human_verified`, `enrichment_source`, territory |
| `builder/wiki_query.py` | Query tab — wiki Q&A with citations |
