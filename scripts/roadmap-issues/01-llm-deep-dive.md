## Summary
One-click (or batch) LLM Deep Dive for papers on **⚓ My Portfolio**: fill `builder/deepdives/<slug>.md` from the full PDF (RQ, method, findings, claims & evidence, limitations).

## Acceptance
- [ ] Trigger from Dive Computer or per-paper action
- [ ] Writes to `builder/deepdives/` and `builder/entries/` — never `wiki/` directly
- [ ] Re-chart after completion; completion state moves to **Deep dive done**
- [ ] Follows `CLAUDE.md` paper source format for generative sections

## Context
- Tier 1 Quick Dip is done (`builder/quick_dip.py`)
- Demo reef: `examples/minimal-vault/` (7 papers)
- Spec: `docs/PAPER-CHART-SPEC.md`
