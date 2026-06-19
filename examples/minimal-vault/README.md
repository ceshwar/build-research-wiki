# Tour vault (demo)

A **fresh example** of the four default docks and three lab papers on the portfolio chart.

| Paper | Venue | PDF |
|-------|-------|-----|
| [Does Positive Reinforcement Work?](wiki/papers/positive-reinforcement-reddit.md) | CHI 2025 | `raw/papers/chi2025-positive-reinforcement.pdf` |
| [The Language of Approval](wiki/papers/language-of-approval.md) | CHI 2026 | `raw/papers/chi2026-language-of-approval-2.pdf` |
| [r/popular Feed Audit](wiki/papers/popular-feed-audit.md) | ICWSM 2026 | `raw/papers/2502.20491v3.pdf` |

## Docks (`builder/docks.yaml`)

| Dock | Folder |
|------|--------|
| ⚓ My Portfolio | `raw/papers/` — the three papers above |
| 🌊 Literature Review | `raw/literature/` — empty (ready for field papers) |
| 🤿 Dive Log | `raw/dive-log/` — empty (transcripts, session notes) |
| 💡 Ideas & Notes | `raw/notes/inbox/` — empty |

Chart entries live in `builder/entries/my-portfolio/`. Deep dives in `builder/deepdives/`.

## Browse

1. Open **`examples/minimal-vault`** in Obsidian.
2. Start at **[index.md](index.md)** → **[wiki/overview.md](wiki/overview.md)**.

## Rebuild

```bash
python3 builder/build.py --vault examples/minimal-vault --full
```

See [docs/GETTING-STARTED.md](../docs/GETTING-STARTED.md) for your own vault.
