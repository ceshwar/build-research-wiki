# Tests

Fixture-based tests for the two pieces of logic whose correctness the product
advertises: **Quick Dip** extraction (the "never guess" contract) and the
**completion** state machine (the Dive Computer's counts).

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
