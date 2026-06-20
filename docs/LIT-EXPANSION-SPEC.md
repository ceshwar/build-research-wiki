# Literature-Expansion Spec — external "related-work" knowledge base

> **Status:** agreed contract, decisions locked 2026-06-19. This is the **build-research-wiki
> mirror** of the spec authored in the portfolio vault — the shared source of truth both
> workstreams build to, so they don't diverge:
> - **(A) reference vault** (`second_brain`) — reference implementation + golden acceptance data.
> - **(B) app + template** (this repo) — the productized ingest engine + UI.
>
> Amendments vs. the original draft are marked **[amended]**; they reconcile the spec with this
> codebase's invariants. Relay them to workstream A so the two copies stay identical.

---

## Decisions locked (2026-06-19)

| # | Decision | Choice |
|---|----------|--------|
| Store location **[amended]** | where fetched OpenAlex data lives | **`builder/lit/store.json`** (generated build input; `raw/` stays immutable) |
| Field-layer home | one vault vs sibling | **same vault, separate `wiki/lit/` folder** |
| Bridge direction | seed_from vs backlinks | **one-directional `seed_from` first** (portfolio backlinks later) |
| Enrichment **[amended]** | how mapped/deepdive tiers are produced | **manual agent** — extend `builder/ingest_prompt.py`; no backend LLM |
| Pilot scope | how far to expand | **hop-1 only**, ranked `seed_from × cited_by_count`, top-N stubs |
| Sequencing | A/B overlap | B builds `engine_lit.py` now vs §1 + synthetic fixture; finalizes `fetch_lit.py` after A's golden slice |

---

## 0. Goal & guiding principle

Grow the wiki beyond Eshwar's papers to the **prior literature in the field**, attaching external
work to the **existing taxonomy** (themes, concepts) so his papers get situated in their citation
neighborhood. **Primary growth signal:** *papers cited by the portfolio* (a reference inside one of
the 49 papers is already vetted). Manual upload (the `lit-review` dock) is the second path;
citation-snowball is the third.

**Non-negotiable:** external literature is a **parallel, clearly-separated layer** (`corpus: field`).
Never mix the two corpora; the graph must distinguish *your* work from *the field's*; field papers
**never** inflate portfolio paper/theme counts.

---

## 1. Shared data model (BOTH workstreams conform)

### Directory layout (additions only; portfolio layout unchanged)
```
builder/lit/store.json        # [amended] generated: one record per external work (metadata + edges)
raw/literature/               # immutable: user-UPLOADED lit PDFs (the existing lit-review dock)
wiki/lit/<slug>.md            # generated: one page per external work (type: extpaper)
wiki/lit/index.md             # generated catalog of the field layer (separate from root index.md)
```
**[amended] Why `builder/lit/` not `raw/lit/`:** `raw/` is immutable in this architecture — the
build never writes there. Fetched OpenAlex data is regenerable machine output (like `auto_*.json`),
so it belongs under `builder/`. Genuinely user-uploaded field PDFs are sources → `raw/literature/`.

### `store.json` record (one per external work)
```json
{
  "slug": "grimmelmann-2015-virtues-of-moderation",
  "ids": { "openalex": "W########", "doi": "10.../...", "arxiv": "####.#####" },
  "title": "...", "authors": ["Last F."], "venue": "...", "year": 2015,
  "url": "<best open link>", "abstract": "<from API; may be empty>",
  "cited_by_count": 0,
  "depth": "stub",                          // stub | mapped | deepdive
  "seed_from": ["portfolio-paper-slug"],    // THE BRIDGE: which portfolio papers cite this
  "discovered_via": "portfolio-citation",   // | manual-upload | snowball
  "themes": [], "concepts": [],             // mapped+ only; MUST be existing data.py slugs
  "one_liner": "", "relates": "",           // mapped+ prose (agent-written into the record)
  "cites": [], "cited_by": [],              // kb-internal slugs only (resolved post-pass)
  "added": "YYYY-MM-DD", "note": ""
}
```
**Source of truth for enrichment:** the agent (manual model) writes structured mapped-tier fields
(`themes`/`concepts`/`one_liner`/`relates`/`depth`) **into the `store.json` record**; deep-dive
*prose* reuses `builder/deepdives/<slug>.md` (same dir + format as the portfolio). `engine_lit.py`
renders both. So `store.json` is the one structured source; no parallel entry files for the field layer.

### `wiki/lit/<slug>.md` frontmatter
`type: extpaper` · `corpus: field` · title/authors/venue/year · `ids` · `url` · `depth` ·
`seed_from` · `discovered_via` · `themes`/`concepts` (mapped+) · `cites`/`cited_by` · `added` · `note`.

### Page body by tier
- **stub:** H1 · metadata line · abstract (from API) · "Cited by your work" (from `seed_from`) ·
  links. No themes/concepts, no deep dive.
- **mapped:** + one-liner · `themes`/`concepts` wikilinks (resolve to *existing* pages) · "How it
  relates to the portfolio" (1–3 sentences).
- **deepdive:** + the standard deep-dive block (RQ · method · findings w/ numbers · claims &
  evidence · limitations) — identical format to `builder/deepdives/`.

### Slug scheme
`lastname-year-keyword`. Canonical identity is `ids.openalex`; on collision append `-b`, `-c`.

### Tiers
| Tier | Produced by | Volume |
|---|---|---|
| **stub** | `engine_lit.py` from `store.json` (deterministic) | hundreds (coverage) |
| **mapped** | **manual agent** via `ingest_prompt.py` (tags themes/concepts + one-liner + bridge) | relevant subset |
| **deepdive** | manual agent, full PDF read | the seminal/adjacent/contested few |

---

## 2. Workstream A — reference vault (`second_brain`)

1. Own/maintain the spec; keep this mirror in sync.
2. Add a short "external literature" section to `CLAUDE.md` (the `wiki/lit/` layer, `type: extpaper`,
   the separation rule).
3. **Empirically validate OpenAlex on the real corpus** and prototype the portfolio→citations
   extraction on **one thread** (content moderation) → the **golden `builder/lit/store.json` slice**
   + generated example pages = B's acceptance target.
4. Confirm 0 red links and that the `seed_from` bridge + concept wikilinks render.

---

## 3. Workstream B — app + template (this repo)

### Build
1. **`builder/engine_lit.py`** *(in progress)* — generic engine: reads `builder/lit/store.json`,
   generates `wiki/lit/<slug>.md` + `wiki/lit/index.md`, resolves `cited_by` post-pass. Plugs into
   `build.py` (after the existing engines); the existing red-link check covers `wiki/lit/` for free.
   Leave `engine_papers.py` / `engine_web.py` untouched.
2. **`builder/fetch_lit.py`** *(after A's slice)* — OpenAlex client → `builder/lit/store.json`.
3. **UI** — the `lit-review` dock already exists for manual upload; add an **"Expand from my
   citations"** action that runs the portfolio→references pipeline.
4. **Enrichment** — extend `builder/ingest_prompt.py` to emit "map these field papers to the
   existing taxonomy / deep-dive these" prompts (manual-agent, consistent with the ingest model).

### Must know (prevents rework / divergence)
- **References from the API, not PDFs.** OpenAlex `referenced_works` (resolved IDs), `cited_by_count`,
  `abstract_inverted_index`, `ids`. **No PDF-bibliography parser.** (Semantic Scholar / Consensus = supplements.)
- **OpenAlex is keyless**; use the polite pool (`mailto` in User-Agent); batch; cache in `builder/lit/`.
- **Reuse the taxonomy.** `themes`/`concepts` on lit pages MUST be existing `data.py` slugs → red-link check.
- **Separation.** `corpus: field`, separate folder + index; never inflate portfolio counts.
- Conform to §1; **A's golden slice is the acceptance test.**

### Guardrails (stricter than the portfolio)
- **Never invent a citation** — every `cites`/`cited_by`/`seed_from` edge comes from the API.
- **Faithfulness flags** — mark from-abstract vs from-full-text; mark paywalled/abstract-only in `note`;
  keep `[external]` labeling.
- **Dedupe on canonical OpenAlex ID** — a paper cited by 5 portfolio papers = ONE page, `seed_from` lists all 5.
- **Scope cap** — pilot = hop-1 only, ranked, top-N; deeper hops stay unwritten stubs-of-record.

---

## 4. Pipeline (cited-by-my-portfolio path)
```
portfolio paper (data.py slug)
  → resolve to OpenAlex work ID (DOI/arXiv/title)
  → GET referenced_works[]                       (papers it cites)
  → fetch metadata for each (batched)            (title/authors/venue/year/abstract/ids/cited_by_count)
  → dedupe by OpenAlex ID; accumulate seed_from[]
  → rank: |seed_from| desc, then cited_by_count; take top-N
  → builder/lit/store.json → engine_lit.py → wiki/lit/ stubs
  → (mapped)  ingest_prompt.py → your agent tags themes/concepts + one-liner + portfolio bridge
  → (deepdive) fetch PDF, full read, deep-dive block
```

---

## 5. Open inputs still needed (small)
- **OpenAlex `mailto`** for the polite pool — propose `eshwarchandrasekharan@gmail.com`. *(confirm)*
- **Golden thread** = content moderation? *(A's call; B just needs the eventual `store.json` slice)*
- **Top-N threshold** per thread for stub materialization (e.g. N=12–20). *(tune on A's data)*
- **Slug collision / author disambiguation** — confirm `-b/-c` suffix is enough at pilot scale.

See also: `CLAUDE.md` (schema) · `builder/README.md` (engine) · `docs/SCUBA-IDEAVERSE.md` (UI).
