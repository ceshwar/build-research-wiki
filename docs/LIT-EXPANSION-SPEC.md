# Literature-Expansion Spec — external "related-work" knowledge base

> **Status:** agreed contract, synced to workstream A's **v2** (2026-06-19). This is the
> **build-research-wiki mirror** of the literature-expansion spec. Two workstreams build to this one contract:
> - **(A) reference vault** — reference implementation + golden acceptance data (private).
> - **(B) app + template** (this repo) — the productized ingest engine + UI.

---

## v2 — locked decisions (2026-06-19, after A's OpenAlex feasibility test + B's review)

**Empirical result (A, on the real corpus):** OpenAlex-by-ID works as the spine — *published*
papers return full reference lists (38–94 refs) that reconstruct into stubs with metadata +
abstracts; ~28% of refs carry a direct OA `pdf_url`. **Gaps:** arXiv-only and very-recent papers
return 0 references; fuzzy *title* resolution mis-matches. → Pipeline **MUST resolve by DOI/arXiv
ID (never title)** and **MUST include a local-PDF reference fallback** for papers OpenAlex can't expand.

- **Storage (Amendment 1 — both agents agree).** `raw/` stays immutable. Generated/fetched data
  lives under `builder/`: **`builder/lit/store.json`** (the record store), **`builder/cache/lit-pdfs/`**
  (auto-fetched OA PDFs for deep dives, refetchable). `raw/literature/` holds **only genuinely
  user-uploaded lit PDFs** (real sources).
- **One field layer (Amendment 2).** The existing **lit-review dock** (manual uploads) and the
  citation-seeded path converge on the **same** `wiki/lit/` + `type: extpaper` pages. `engine_lit.py`
  supersedes the `wiki/sources/` shell **for the literature dock specifically** (dive-log/notes docks
  unaffected). Provenance is carried by `discovered_via`, not by a different page type.
- **Manual-agent enrichment (Amendment 3).** Stub generation is deterministic (`fetch_lit.py` +
  `engine_lit.py`, no backend LLM). `mapped`/`deepdive` tiers are produced by the user's agent via an
  extension of `builder/ingest_prompt.py`. No automated tagger.
- **§5 locked:** one vault + separate `wiki/lit/`; single JSON store; one-directional `seed_from`
  bridge first; slug `lastname-year-keyword` (`-b/-c` on collision, canonical identity = `ids.openalex`).
- **Hop-1 scope (locked 2026-06-19):** *hop-1 only, no snowball.* After dedupe by OpenAlex ID and
  `seed_from` accumulation, **materialize only the top N candidates as stubs** — default
  **`sort_by: year` (desc, most recent first), `limit: 10`**. Users may override `sort_by` and
  `limit` (`limit: all` = no cap). See **§1.1 Hop-1 stub selection** below. Promotion to
  **mapped** / **deepdive** is a separate, smaller cap (agent-driven; unchanged).

---

## 1. Shared data model (BOTH workstreams conform)

### Directory layout (additions only; portfolio layout unchanged)
```
raw/literature/              # immutable: ONLY user-uploaded lit PDFs (real sources)
builder/lit/store.json       # GENERATED: one record per external work (metadata + edges)
builder/cache/lit-pdfs/      # GENERATED: auto-fetched OA PDFs for deep dives (refetchable)
wiki/lit/<slug>.md           # GENERATED: one page per external work (type: extpaper)
wiki/lit/index.md            # GENERATED: field-layer catalog (separate from root index.md)
```
Invariant: `raw/` = human-curated & immutable; `builder/` = regenerable machine output.

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
  "cites": [], "cited_by": [],              // kb-internal slugs only (cited_by derived post-pass)
  "added": "YYYY-MM-DD", "note": ""
}
```
**B implementation note (engine_lit.py reads this):** the agent writes the structured mapped-tier
fields (`themes`/`concepts`/`one_liner`/`relates`/`depth`) **into the record**; deep-dive *prose*
reuses `builder/deepdives/<slug>.md`. `engine_lit.py` derives `cited_by` from `cites` post-pass —
so A's golden store only needs to supply `cites` (refs that are themselves in the KB).

### `wiki/lit/<slug>.md` frontmatter
`type: extpaper` · `corpus: field` · title/authors/venue/year · `ids` · `url` · `depth` ·
`seed_from` · `discovered_via` · `themes`/`concepts` (mapped+) · `cites`/`cited_by` · `added` · `note`.

### Page body by tier
- **stub:** H1 · metadata · abstract (from API, `[external]`) · "Cited by your work" (from `seed_from`) · links.
- **mapped:** + one-liner · `themes`/`concepts` wikilinks (resolve to existing pages) · "How it relates to the portfolio."
- **deepdive:** + standard deep-dive block (RQ · method · findings w/ numbers · claims & evidence · limitations).

### §1.1 Hop-1 stub selection (configurable cap)

After `fetch_lit.py` resolves portfolio papers → OpenAlex `referenced_works[]` → batched metadata,
records are **deduped** (canonical `ids.openalex`), **`seed_from[]` merged**, then **ranked and
truncated** before write to `builder/lit/store.json`.

| Setting | Default | Values | Notes |
|---------|---------|--------|-------|
| **`sort_by`** | `year` | `year` · `seed_count` · `cited_by_count` | Descending. `year` = `publication_year` (missing year → sort last). `seed_count` = &#124;`seed_from`&#124;. `cited_by_count` = OpenAlex field. **Tie-break** (when the primary key ties): `cited_by_count` desc, then `seed_count` desc. |
| **`limit`** | `10` | positive integer · `all` | Max stubs **materialized** this run. `all` = every deduped hop-1 candidate. |

**Rationale:** Recent cited work is the usual priority for lit review; older classics remain
reachable via `sort_by: cited_by_count` or `limit: all`. The expensive step is agent **mapped/deepdive**,
not stub metadata.

**Sort key (implementation):** Python-style tuple sort, descending:

```python
# sort_by selects which field is primary; ties always break the same way:
primary = {"year": year_or_0, "seed_count": len(seed_from), "cited_by_count": cited_by_count}[sort_by]
key = (primary, cited_by_count, len(seed_from))   # all descending; missing year → 0 (last)
```

Example: `sort_by: year`, two 2021 papers → higher `cited_by_count` wins; if still tied, higher `seed_count`.

**Config surfaces (all must agree on defaults):**

```yaml
# builder/lit/config.yaml  (per vault; created on first expand if missing)
hop1:
  sort_by: year      # year | seed_count | cited_by_count
  limit: 10            # integer or "all"
mailto: you@example.edu   # OpenAlex polite pool (required for live fetch)
```

CLI mirrors config: `fetch_lit.py --sort-by year --limit 10` · `--limit all`  
UI (planned): **Expand from my citations** → advanced row with the same two fields.

**Merge policy on re-run:** Replace only records where `discovered_via: portfolio-citation` and
`depth: stub` that are **not** in the new top-N set (demote to archive or drop — B implements
**drop** for MVP; log count of dropped stubs). Preserve `manual-upload`, `mapped`, and `deepdive`
records regardless of rank.

**Store metadata (optional, on each stub record):**

```json
"selection": { "sort_by": "year", "limit": 10, "rank": 3, "candidates_total": 184 }
```

`rank` = 1-based position after sort (for UI/debug). `candidates_total` = hop-1 pool size before truncation.

**Worked example (moderation thread, illustrative):** 4 seeds → 184 unique hop-1 refs. Default
`year` + `limit: 10` might surface 2016–2021 Reddit/governance papers; `cited_by_count` + `limit: 10`
might surface Lessig 1999; `limit: all` materializes all 184 stubs (user opt-in).

### Tiers
| Tier | Produced by | Volume |
|---|---|---|
| **stub** | `fetch_lit.py` → `engine_lit.py` | top **N** hop-1 by `sort_by` (default **10**, `year`) |
| **mapped** | manual agent via `ingest_prompt.py` (`seed_from ≥ 2`) | subset of stubs — agent chooses |
| **deepdive** | manual agent, full PDF read | small hand-picked set (e.g. top 5 by `seed_count` or user list) |

---

## 2. Workstream A — reference vault
Own/maintain the canonical spec; add the external-lit section to `CLAUDE.md`; run the OpenAlex
extraction on the **content-moderation thread** → the golden `builder/lit/store.json` slice +
example pages = B's acceptance target; confirm 0 red links + the `seed_from` bridge renders.

## 3. Workstream B — app + template (this repo)
1. **`builder/engine_lit.py`** — ✅ built: deterministic renderer (`store.json` → `wiki/lit/` + index,
   `cited_by` post-pass, idempotent write-if-changed, reuses existing slugs). Wired into `build.py`;
   shared red-link check covers `wiki/lit/`.
2. **`builder/fetch_lit.py`** — *after A's slice:* OpenAlex client → `builder/lit/store.json`.
   **Resolve by DOI/arXiv ID, never title.** API-references primary; **local-PDF References parsing
   (GROBID/anystyle/LLM, not regex) is the required FALLBACK** when OpenAlex returns 0 refs.
3. **UI** — "Expand from my citations" action; the lit-review dock feeds the same `wiki/lit/` layer.
4. **Enrichment** — extend `builder/ingest_prompt.py` for lit `mapped`/`deepdive` (manual agent).

### Guardrails (stricter than portfolio)
Never invent a `cites`/`cited_by`/`seed_from` edge (all from API/PDF refs). Dedupe on canonical
OpenAlex ID (cited by 5 papers = ONE page, `seed_from` lists 5). `corpus: field`; never inflate
portfolio counts. Faithfulness flags: from-abstract vs from-full-text; paywalled in `note`; `[external]`.

---

## 4. Pipeline (cited-by-my-portfolio path)
```
portfolio paper (data.py slug)
  → resolve to OpenAlex work ID via DOI / arXiv ID      (NEVER fuzzy title — mis-matches)
  → GET referenced_works[]
  → IF empty (arXiv preprint / recent):  parse local raw/papers/<pdf> References
        (GROBID/anystyle/LLM over the section, NOT regex) → reconcile each to OpenAlex   [required fallback]
  → fetch metadata per ref (batched): title/authors/venue/year/abstract/ids/cited_by_count/oa_url
  → dedupe by canonical OpenAlex ID; accumulate seed_from[]
  → rank by sort_by (default year desc); truncate to limit (default 10; or all)
  → builder/lit/store.json → engine_lit.py → wiki/lit/ stubs (deterministic)
  → (mapped)   agent tags themes/concepts + one-liner + bridge via ingest_prompt.py (manual model)
  → (deepdive) fetch OA pdf_url → builder/cache/lit-pdfs/ → full read → deep-dive block
```

## 5. Open inputs
Confirm OpenAlex `mailto` for polite pool; golden thread = content moderation (acceptance slice).
**Hop-1 stub scope: locked** — default `sort_by: year`, `limit: 10`, user-overridable incl. `all`.
Snowball / forward-citations = post-pilot. **Pending:** `fetch_lit.py` + UI must implement §1.1
(current code ranks by `seed_count` then `cited_by_count` and has no limit).

See also: `CLAUDE.md` · `builder/README.md` · `docs/SCUBA-IDEAVERSE.md`.
