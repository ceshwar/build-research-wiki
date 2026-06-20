# Shallow reef (demo)

Pre-loaded trial reef for SCUBA Ideaverse — demo papers in `examples/minimal-vault`.

A **hybrid demo**: three fully enriched lab papers plus four **Quick Dip** papers on the Healthy Online Behavior thread (ready for agent Deep Dive).

## Charted (Deep dive done) — 3

| Paper | Venue | PDF |
|-------|-------|-----|
| [Does Positive Reinforcement Work?](wiki/papers/positive-reinforcement-reddit.md) | CHI 2025 | `chi2025-positive-reinforcement.pdf` |
| [The Language of Approval](wiki/papers/language-of-approval.md) | CHI 2026 | `chi2026-language-of-approval-2.pdf` |
| [r/popular Feed Audit](wiki/papers/popular-feed-audit.md) | ICWSM 2026 | `2502.20491v3.pdf` |

## Quick Dip (enrich next) — 4

| Paper | Venue | PDF |
|-------|-------|-----|
| [Creator Hearts](wiki/papers/creator-hearts.md) | CHI 2025 | `chi2025-creator-hearts-2.pdf` |
| [Hidden Values / Highly-Upvoted](wiki/papers/hidden-values-upvoted.md) | ICWSM 2026 | `2410.13036.pdf` |
| [Moderator Perspectives on Positive Reinforcement](wiki/papers/mod-perspectives-pos-reinforcement.md) | CSCW 2024 | `cscw2024_positive_reinforcement.pdf` |
| [Mind Your Ps and Qs (Positive Queue)](wiki/papers/mind-your-ps-and-qs.md) | CSCW 2027 | `2509.18437v1-2.pdf` |

In SCUBA: **Get ingest prompt** on ⚓ My Portfolio lists these four. Paste into Claude Code to fill themes, one-liners, and `builder/deepdives/`.

## Docks (`builder/docks.yaml`)

| Dock | Folder |
|------|--------|
| ⚓ My Portfolio | `raw/papers/` — seven PDFs above |
| 🌊 Literature Review | `raw/literature/` — empty |
| 🤿 Dive Log | `raw/dive-log/` — empty |
| 💡 Ideas & Notes | `raw/notes/inbox/` — empty |

## Browse

1. Open **`examples/minimal-vault`** in Obsidian.
2. Start at **[index.md](index.md)** → **[wiki/overview.md](wiki/overview.md)**.

## Rebuild

```bash
python3 builder/build.py --vault examples/minimal-vault --full
```

See [docs/GETTING-STARTED.md](../docs/GETTING-STARTED.md) for spawning your own reef.
