# Getting started

This guide helps you go from **clone** to **working research wiki** in one session.

- **Shallow reef** — pre-loaded demo at [`examples/minimal-vault/`](../examples/minimal-vault/) (7 papers; safe to explore).
- **Blank reef** — empty scaffold at the repo root (`CLAUDE.md`, `raw/`, starter `builder/`). Copy it or run `new_vault.py` for your lab.

**Pattern credit:** This repo implements the [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern — a persistent, compounding Markdown knowledge base maintained by an LLM assistant, not re-derived from raw PDFs on every question.

---

## First-session checklist (~30 minutes)

- [ ] **Clone** the repo and open the folder in your LLM coding agent (Cursor, Claude Code, Codex, etc.).
- [ ] **Start SCUBA** — `./manager/scripts/dev.sh` → **http://127.0.0.1:5173**.
- [ ] **Pick Shallow reef** in the header dropdown — explore the Dive Computer, portfolio map (List / By theme), and **Docs** (in-app glossary).
- [ ] **Browse in Obsidian** — open `examples/minimal-vault`; read `index.md` → `wiki/overview.md` → one paper page.
- [ ] **Try Get ingest prompt** — on Shallow reef, ⚓ My Portfolio → **Get ingest prompt** → paste into your agent to Deep Dive the four Quick Dip papers.
- [ ] **Spawn your own reef** — **+ Connect your reef…** or `python3 builder/new_vault.py ~/path "Lab Name"`.
- [ ] **Dock one PDF** — upload to ⚓ My Portfolio, confirm, watch Quick Dip run.
- [ ] **Query** — ask your agent: *"What do my sources say about X?"* Offer to file a good answer into `wiki/syntheses/`.
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

1. **Clone** the team's reef repo (not the Blank reef scaffold).
2. Open as an Obsidian vault — explore `index.md` and `wiki/overview.md`.
3. **Read** [`docs/TEAM-COLLABORATION.md`](TEAM-COLLABORATION.md) for commit norms and what not to edit.
4. To add papers: drop files in `raw/`, then ask the team (or your agent) to ingest. For builder-managed papers, follow Path B steps 2–5 and open a PR.

### Path D — "SCUBA Ideaverse" (UI workflow) — *recommended for labs*

Best for teams who want a visual dock-and-chart workflow without typing ingest commands.

1. Clone the repo and run `./manager/scripts/dev.sh`.
2. Open **http://127.0.0.1:5173**.
3. Pick **Shallow reef** (demo) or **Blank reef** (empty scaffold). Use **+ Connect your reef…** to register your own Obsidian folder (saved locally, gitignored).
4. **Dock** — collapse-open the upload panel, drop PDFs, **Confirm Upload** → `raw/{channel}/`.
5. **Quick Dip** — runs automatically for portfolio uploads; or click **Update chart**.
6. **Portfolio map** — browse charted papers (List or By theme tabs); click Obsidian links to open pages.
7. **Deep Dive** — **Get ingest prompt** copies an agent-ready batch prompt; or edit `builder/entries/` and `builder/deepdives/` by hand.
8. Check the **Dive Computer** — **On chart**, **Quick dip**, **Enrich next**, **Awaiting chart** tell you what still needs work.
9. Open the reef in Obsidian (header icon or portfolio map links).

See [`docs/SCUBA-IDEAVERSE.md`](SCUBA-IDEAVERSE.md) and the in-app **Docs** panel for SCUBA vocabulary.

---

## Requirements

| Tool | Required? | Purpose |
|------|-----------|---------|
| Python 3.7+ | **Yes** (for SCUBA + builder) | Backend + chart generator |
| Node 18+ | **Yes** (for SCUBA UI) | Frontend dev server |
| LLM coding agent | **Yes** (for Deep Dive / ingest) | Reads/writes wiki files; follows `CLAUDE.md` |
| [Obsidian](https://obsidian.md) | Recommended | Browse links, graph view, Dataview |
| [poppler](https://poppler.freedesktop.org/) | Optional | PDF text extraction (`brew install poppler`) |

### Agent compatibility

- **Cursor / Claude Code** — reads `CLAUDE.md` automatically.
- **OpenAI Codex / other agents** — read `AGENTS.md` (points to the same schema).
- Any agent that can read and write files in a folder works.

---

## Make it yours

1. Edit **`CLAUDE.md` §9** — set your domain, venues, and field-specific conventions.
2. Fill **`builder/data.py`** `VAULT` metadata (`name`, `owner`, `domain`).
3. Replace **`wiki/overview.md`** placeholder with your lab's research threads.

---

## See also

- [SCUBA Ideaverse](SCUBA-IDEAVERSE.md) — dock, chart, completion tracking, reefs
- [Shallow reef (demo)](../examples/minimal-vault/) — 7 papers on chart
- [Team collaboration](TEAM-COLLABORATION.md) — shared repos, git norms, privacy
- [Changelog](CHANGELOG.md) — release notes
- [README](../README.md) — product overview
- [BUILD.md](../BUILD.md) — deterministic builder
