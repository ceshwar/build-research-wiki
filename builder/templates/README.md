# SCUBA entry templates

Copy any file here into `builder/entries/<channel>/` to start a new chart entry by hand.

On **Surface Interval**, unmapped dock artifacts get an entry file created automatically
from the matching template. Edit the entry file — not `raw/` — then re-run Surface Interval.

| Channel | Template | Entry | Deep dive |
|---------|----------|-------|-----------|
| my-portfolio | `my-portfolio/entry.md` | `builder/entries/my-portfolio/<slug>.md` | `builder/deepdives/<slug>.md` |
| lab-portfolio | `lab-portfolio/entry.md` | `builder/entries/lab-portfolio/<slug>.md` | `builder/deepdives/<slug>.md` |
| lit-review | `lit-review/entry.md` | `builder/entries/lit-review/<slug>.md` | `builder/deepdives/<slug>.md` |
| concepts | `concepts/entry.md` | copy by hand | — |

**Paper page shape** (matches a fleshed-out `wiki/papers/` entry like *beyond-throughput*):

| Section | Filled by | Where you edit |
|---------|-----------|----------------|
| Frontmatter, title, venue, year | Surface Interval (deterministic) | `builder/data.py` / auto registry |
| One-liner `>` quote | You or LLM | `## One-liner` in entry file |
| Themes | You or LLM | `[[wikilinks]]` on line 1 of entry |
| Abstract / Notes | You or LLM | `## Abstract` in entry file |
| Deep dive (RQ, method, findings, …) | LLM Deep Dive or manual | `builder/deepdives/<slug>.md` |

**Completion states** (shown on Dive Computer):

- **Pending** — docked in `raw/` but not surfaced yet
- **Scaffolded** — on chart; themes, abstract, or one-liner still empty
- **Charted** — deterministic parts filled; deep dive still pending
- **Processed** — fully charted including deep dive

Uploads stay in `raw/` only. They are never modified by the chart build.
