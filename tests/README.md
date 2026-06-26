# Tests

Fixture-based tests for the two pieces of logic whose correctness the product
advertises: **Quick Dip** extraction (the "never guess" contract) and the
**completion** state machine (Chart status counts).

```bash
pip install -r requirements-dev.txt   # pytest
python3 -m pytest                      # from the repo root
```

Fixtures use the three real PDFs in `examples/minimal-vault/raw/papers/`, so the
tests exercise the actual extraction path end-to-end — no mocked PDF text.

- `test_quick_dip.py` — title/abstract/venue/year extraction; year-sanity guard
  (regression for arXiv ids leaking implausible years); no fabricated sections.
- `test_completion.py` — pending → quick_dip → needs_deep_dive → processed
  classification, plus the helper predicates.
- `manager/frontend/src/lib/wikiLinks.test.ts` — Query citation link parsing
  (`[[wikilink]]`, `[label](slug)`, `portolan://` resolution).
- `test_fetch_lit.py` / `test_engine_lit.py` — lit expansion transforms + `wiki/lit/` render
  (hop-1 **selection policy** in `docs/LIT-EXPANSION-SPEC.md` §1.1 — tests to add when implemented).

## QA checklist (run anytime)

```bash
pip install -r requirements-dev.txt
python3 -m pytest -q                              # unit tests
(cd manager/frontend && npm test)                 # frontend wiki-link tests
python3 builder/qa_quick_dip.py                   # Tier-1 no-guess contract
python3 builder/build.py --vault examples/minimal-vault
python3 builder/ingest_prompt.py --vault examples/minimal-vault --channel my-portfolio
```

Manual / integration (no A/B dependency):

| Check | Command / action | Pass criterion |
|-------|------------------|----------------|
| Red links | `build.py` output | `red links: NONE` |
| Ingest prompt API | `curl localhost:8000/ingest-prompt?vault_id=demo&channel_id=my-portfolio` | JSON `prompt` + `count` |
| Registry round-trip | `pytest tests/test_registry.py` | JSON load/save, legacy `.py` migration |
| Lit engine idempotent | `pytest tests/test_engine_lit.py` | `wiki/lit/` pages, no red links on demo slugs |
| Fetch transforms | `pytest tests/test_fetch_lit.py` | slugify, seed_from merge, dedupe |
| UI ingest section | dev server → Get ingest prompt | Prompt lists quick-dip items; copy works |
| Spec ↔ code drift | read `docs/LIT-EXPANSION-SPEC.md` §1.1 vs `fetch_lit.rank()` | Document gaps until B implements sort/limit |
