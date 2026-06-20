# Literature-Expansion Spec — external "related-work" knowledge base

> **Status:** agreed contract, synced to workstream A's **v2** (2026-06-19). This is the
> **build-research-wiki mirror**; the canonical copy is `second_brain/LIT-EXPANSION-SPEC.md`
> (workstream A owns/edits it, B mirrors). Two workstreams build to this one contract:
> - **(A) reference vault** (`second_brain`) — reference implementation + golden acceptance data.
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
- **Scope cap (⚠ B-flag — needs your confirm):** A's v2 = *hop-1 only, no snowball*; **materialize
  ALL hop-1 refs as stubs**, promote to **mapped** at `seed_from ≥ 2`, **deep-dive** the top ~5–10 by
  in-KB citation count. **This overrides the "top-N stubs" answer from B's interview** — Eshwar to
  confirm "all hop-1 stubs" vs "top-N stubs" (stubs are cheap, so A's call is reasonable; the real
  cost cap is at mapped/deepdive).

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

### Tiers
| Tier | Produced by | Volume |
|---|---|---|
| **stub** | `engine_lit.py` from `store.json` (deterministic) | all hop-1 refs (coverage) |
| **mapped** | manual agent via `ingest_prompt.py` (`seed_from ≥ 2`) | the cited-twice subset |
| **deepdive** | manual agent, full PDF read | top ~5–10 by in-KB citations |

---

## 2. Workstream A — reference vault (`second_brain`)
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
  → dedupe by canonical OpenAlex ID; accumulate seed_from[]; rank |seed_from| desc, then cited_by_count
  → builder/lit/store.json → engine_lit.py → wiki/lit/ stubs (deterministic)
  → (mapped)   agent tags themes/concepts + one-liner + bridge via ingest_prompt.py (manual model)
  → (deepdive) fetch OA pdf_url → builder/cache/lit-pdfs/ → full read → deep-dive block
```

## 5. Open inputs
Confirm OpenAlex `mailto` = `eshwarchandrasekharan@gmail.com`; golden thread = content moderation;
**resolve the stub scope ⚠ (all hop-1 vs top-N)**. Snowball / forward-citations = post-pilot.

See also: `CLAUDE.md` · `builder/README.md` · `docs/SCUBA-IDEAVERSE.md` · `second_brain/LIT-EXPANSION-SPEC.md` (canonical).
