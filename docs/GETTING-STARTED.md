# Getting started

This guide helps you go from **clone** to **working research wiki** in one session. The blank template lives at the repo root; a populated tour vault lives in [`examples/minimal-vault/`](../examples/minimal-vault/).

**Pattern credit:** This vault implements the [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern — a persistent, compounding Markdown knowledge base maintained by an LLM assistant, not re-derived from raw PDFs on every question.

---

## First-session checklist (~30 minutes)

- [ ] **Clone** the repo and open the folder in your LLM coding agent (Cursor, Claude Code, Codex, etc.).
- [ ] **Browse the demo** — open `examples/minimal-vault` in Obsidian; read `index.md` → `wiki/overview.md` → one paper page.
- [ ] **Copy the blank template** for your own work (stay at repo root, or run `python3 builder/new_vault.py ~/path "Lab Name"`).
- [ ] **Add one source** — drop a PDF into `raw/papers/` (or a Markdown note into `raw/notes/`).
- [ ] **Ingest** — tell your agent: *"Ingest the new files in `raw/`."* (It reads [`CLAUDE.md`](../CLAUDE.md) / [`AGENTS.md`](../AGENTS.md).)
- [ ] **Browse** — open your vault in Obsidian; follow wikilinks and graph view.
- [ ] **Query** — ask: *"What do my sources say about X?"* Offer to file a good answer into `wiki/syntheses/`.
- [ ] **Optional lint** — ask: *"Lint the wiki"* to surface orphans, red links, and contradictions.

---

## Choose your path

### Path A — "I have PDFs, no structure yet"

Best if you're starting fresh or have a pile of papers without curated notes.

1. Copy PDFs into `raw/papers/` (any filename is fine).
2. Open the folder in an LLM agent and say: **"Ingest the new files in `raw/`."**
3. The assistant creates `wiki/sources/` pages, updates entities/concepts, and maintains `index.md` + `log.md`.
4. Browse in Obsidian. Ask questions; file syntheses back into `wiki/syntheses/`.

**You can skip the builder entirely** on this path. See [`CLAUDE.md`](../CLAUDE.md) §6 (ingest / query / lint).

### Path B — "I have a paper portfolio with themes"

Best if you organize work by research theme and want a reproducible portfolio map.

1. Add PDFs to `raw/papers/`.
2. **Quick Dip** — UI (auto after dock on portfolio) or `python3 builder/map_channel.py --channel my-portfolio` — extracts PDF title/abstract/venue/year into `builder/entries/my-portfolio/<slug>.md` (no theme placeholders).
3. **Deep Dive** — add `[[theme-slug]]` wikilinks, `## One-liner`, and `builder/deepdives/<slug>.md`.
4. Add theme definitions to `builder/data.py` and theme one-liners in `raw/notes/themes/` (optional).
5. Register hand-curated papers in `builder/data.py` (see `examples/minimal-vault/builder/data.py`).
6. Run `python3 builder/build.py`.
7. Write deep dives in `builder/deepdives/<slug>.md` and re-run the build.
8. Hand-update `wiki/overview.md`; append to `log.md`.

Legacy: abstract notes in `raw/notes/abstracts/` still work if referenced from `data.py`.

See [`BUILD.md`](../BUILD.md), [`builder/README.md`](../builder/README.md), or Path D for the UI.

### Path C — "I'm joining an existing team wiki"

1. **Clone** the team's vault repo (don't use the blank template).
2. Open as an Obsidian vault — explore `index.md` and `wiki/overview.md`.
3. **Read** [`docs/TEAM-COLLABORATION.md`](TEAM-COLLABORATION.md) for commit norms and what not to edit.
4. To add papers: drop files in `raw/`, then ask the team (or your agent) to ingest. For builder-managed papers, follow Path B steps 2–5 and open a PR.

### Path D — "SCUBA Ideaverse" (UI workflow)

Best for teams who want a visual dock-and-chart workflow without typing ingest commands.

1. Clone the repo and run `./manager/scripts/dev.sh`.
2. Open **http://127.0.0.1:5173** — pick the tour vault (`examples/minimal-vault`) or your own (configure `manager/backend/config/vaults.yaml`).
3. **Dock** a PDF into a channel → **Confirm Upload** (lands in `raw/`).
4. **Surface Interval** — scaffolds `builder/entries/` from templates and rebuilds `wiki/`.
5. Edit the entry file (themes, abstract, one-liner) and `builder/deepdives/<slug>.md`.
6. Check the **Dive Computer** — **Processed** vs **Needs review** tells you what still needs work.
7. Open the reef in Obsidian.

See [`docs/SCUBA-IDEAVERSE.md`](SCUBA-IDEAVERSE.md).

---

## Requirements

| Tool | Required? | Purpose |
|------|-----------|---------|
| LLM coding agent | **Yes** (for ingest/query) | Reads/writes wiki files; follows `CLAUDE.md` |
| [Obsidian](https://obsidian.md) | Recommended | Browse links, graph view, Dataview |
| Python 3 | Optional | Portfolio builder (`builder/build.py`) |
| [poppler](https://poppler.freedesktop.org/) | Optional | PDF text extraction (`builder/extract_pdfs.py`) |

### Agent compatibility

- **Cursor / Claude Code** — reads `CLAUDE.md` automatically.
- **OpenAI Codex / other agents** — read `AGENTS.md` (symlinked to the same schema).
- Any agent that can read and write files in a folder works.

---

## Make it yours

1. Edit **`CLAUDE.md` §9** — set your domain, venues, and field-specific conventions.
2. Fill **`builder/data.py`** `VAULT` metadata (`owner`, `domain`).
3. Replace **`wiki/overview.md`** placeholder with your lab's research threads.

---

## See also

- [SCUBA Ideaverse](SCUBA-IDEAVERSE.md) — dock, surface, completion tracking
- [Tour vault (demo)](../examples/minimal-vault/) — three papers on chart
- [Team collaboration](TEAM-COLLABORATION.md) — shared repos, git norms, privacy
- [Changelog](CHANGELOG.md) — v0.3.0 release notes
- [README](../README.md) — product overview
- [BUILD.md](../BUILD.md) — deterministic builder
