# SCUBA entry templates

Templates are for **hand-starting** entries or reference. **Quick Dip** does not copy these — it writes a minimal PDF-fact entry via `builder/quick_dip.py`.

On **Update chart (Quick Dip)**, unmapped dock artifacts get a Tier 1 entry automatically. **Deep Dive** (later) enriches themes, one-liner, and `builder/deepdives/`.

| Channel | Template | Entry | Deep dive |
|---------|----------|-------|-----------|
| my-portfolio | `my-portfolio/entry.md` | `builder/entries/my-portfolio/<slug>.md` | `builder/deepdives/<slug>.md` |
| lab-portfolio | `lab-portfolio/entry.md` | `builder/entries/lab-portfolio/<slug>.md` | `builder/deepdives/<slug>.md` |
| lit-review | `lit-review/entry.md` | `builder/entries/lit-review/<slug>.md` | `builder/deepdives/<slug>.md` |
| concepts | `concepts/entry.md` | copy by hand | — |

See [`docs/PAPER-CHART-SPEC.md`](../docs/PAPER-CHART-SPEC.md) for the full Tier 1 / Tier 2 spec.

**Paper page shape** (finished state, like *beyond-throughput*):

| Section | Quick Dip | Deep Dive |
|---------|-----------|-----------|
| Frontmatter, title, venue, year | PDF facts only | confirm/correct in registry |
| One-liner `>` quote | — | entry `## One-liner` |
| Themes | — | `[[wikilinks]]` line 1 of entry |
| Abstract | PDF text if found | edit entry if PDF missed it |
| Deep dive (RQ, method, findings, …) | — | `builder/deepdives/<slug>.md` |

**Completion states** (Dive Computer):

- **Pending** — docked in `raw/` but not charted
- **Quick dip** — Tier 1 on chart (PDF facts)
- **Needs deep dive** — themes/abstract/one-liner done; analysis pending
- **Deep dive done** — fully enriched

Uploads stay in `raw/` only. They are never modified by the chart build.
