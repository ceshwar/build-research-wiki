# Paper chart spec — Uncharted · Quick Dip · Deep Dive

Chart entries are **product IP**: structured wiki pages we generate for users. **Update chart** surfaces factual metadata without guessing; **Quick Dip (LLM)** fills generative sections; **Deep dive** means human-verified.

---

## Trust tiers (user-facing)

| Tier | UI label | Meaning |
|------|----------|---------|
| **0** | **Uncharted** ◎ | On chart, not LLM-ingested — PDF/metadata only (`status: quick-dip` registry row) |
| **1** | **Quick dip** 🤿 | LLM-ingested — `llm_enriched: true`, awaiting human review |
| **2** | **Deep dive** 🦑 | Verified — `human_verified: true` (or trusted hand-`mapped`) |

**Pipeline:** Dock → **Update chart** (Uncharted) → **Run Quick Dip (LLM)** → review → mark verified → **Deep dive**.

---

## Tiers (implementation)

| Tier | Name | Trigger | What gets filled |
|------|------|---------|-------------------|
| **1** | **Surface chart** | Dock + **Update chart** | PDF-derived facts only → **Uncharted** |
| **2** | **Quick Dip (LLM)** | **Run Quick Dip** in Actions | Themes, one-liner, deep dive sections |
| **3** | **Deep dive** | Mark verified in Portolan | Trust gate — same wiki content, verified flag |

Registry `status: quick-dip` means “PDF surfaced on chart” (Uncharted), not the UI label Quick dip.

---

## Surface chart (Tier 1) — rules

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

### Forbidden in surface chart output

- `venue: unknown`
- `[[theme-slug]]` or similar template placeholders
- `Auto-mapped from PDF`, `Docked PDF`, `fill themes`, `Pending LLM` boilerplate in entry body
- Filename used as title when PDF text is unavailable
- Today's date as publication year

### Where it lands

```
raw/papers/foo.pdf                          # immutable upload
builder/entries/my-portfolio/foo.md         # surface entry (edit here)
builder/auto_papers.json                    # registry row (status: quick-dip)
wiki/papers/foo.md                          # generated chart page
```

Entry file header:

```markdown
<!-- chart-tier: quick-dip — PDF-derived fields only; run Quick Dip (LLM) to enrich -->

## Abstract
<text from PDF or empty>

## One-liner

## My notes
```

---

## Quick Dip (LLM)

**In-app:** Actions → **Run Quick Dip (LLM)** calls `builder/deep_dive_llm.py` via Ollama (default **qwen3:32b**). Writes `builder/entries/`, `builder/deepdives/`, sets `llm_enriched: true` — lands in **Quick dip** until you mark verified → **Deep dive**.

User, frontier model, or agent can also enrich manually:

1. **Themes** — `[[wikilinks]]` on line 1 of `builder/entries/<channel>/<slug>.md`
2. **One-liner** — `## One-liner` in entry file
3. **Deep dive** — `builder/deepdives/<slug>.md` (RQ, method, findings, limitations, …)
4. Optional: concept/entity pages, synthesis updates

Re-run **Update chart** after edits to refresh `wiki/`.

### Enrichment sources (stored in `builder/verification.json` + wiki frontmatter)

| `enrichment_source` | Meaning |
|---------------------|---------|
| `quick-dip` | Tier 1 PDF surface only (Uncharted) |
| `local-32b` | Quick Dip (LLM) via local Ollama |
| `local-custom` | LLM Deep Dive via another local model |
| `frontier` | LLM Deep Dive via Anthropic/OpenAI |
| `human` | Hand-charted / user-verified corpus |

### Territory (`territory` frontmatter)

| `territory` | Meaning |
|-------------|---------|
| `uncharted` | Not LLM-ingested (`llm_enriched: false`) |
| `quick_dip` | LLM-ingested, awaiting review |
| `charted` | Deep dive — human-verified |

Mark **Deep dive verified** in Portolan after reading; wiki gets `human_verified: true` and a callout.

---

## Completion states (internal)

| State | UI mapping |
|-------|------------|
| **Pending** | Awaiting chart |
| **quick_dip / needs_deep_dive / scaffolded** | Usually **Uncharted** (no LLM yet) |
| **processed + llm_enriched + !verified** | **Quick dip** |
| **processed + human_verified** | **Deep dive** |

---

## UI flow

1. User docks a PDF → **Confirm upload**
2. **Update chart** surfaces PDF metadata (**Uncharted**)
3. **Run Quick Dip (LLM)** when Ollama is available
4. Review in Navigate → mark **Deep dive verified**
5. **Query** with scope: All · Deep dive · Quick dip · Uncharted

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
