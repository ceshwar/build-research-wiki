# build-research-wiki

Build your own **LLM-powered research wiki** — a persistent, compounding knowledge base that
an AI assistant (Claude Code, or any LLM agent that can read files) maintains for you. You drop
in papers and notes; the assistant reads them, summarizes them, cross-links entities and
concepts, flags contradictions, and files everything as plain Markdown you browse in
[Obsidian](https://obsidian.md).

It's just a folder of Markdown. No database, no server, no lock-in. The "intelligence" lives in
one schema file (`CLAUDE.md`) that tells the assistant how to read and file things, plus an
optional Python builder for reproducible, scriptable rebuilds.

```
raw/  ──(you add papers)──►  assistant reads + files  ──►  wiki/  ──►  open in Obsidian
```

---

## Two ways to use it

You can use either, or both. Both produce the same kind of plain-Markdown, Obsidian-friendly
wiki.

### 1. LLM-driven ingest (the main workflow)
Drop documents into `raw/`, open the folder in an LLM coding agent (e.g. Claude Code), and say:

> *"Ingest the new papers in `raw/`."*

The assistant reads [`CLAUDE.md`](CLAUDE.md) — the operating manual — and does the rest:
writes a summary page per source, updates/creates entity and concept pages, links everything
bidirectionally, flags contradictions, and updates `index.md` + `log.md`. Then ask it
questions (*"What do my sources say about X?"*) and file the good answers back as syntheses.

Works with **PDFs, Markdown, text, transcripts, images** — anything the assistant can read.

### 2. Deterministic builder (optional, scriptable)
For the specific pattern of mapping a **paper portfolio by research theme**, the `builder/`
directory generates that slice of the wiki from a single data file — idempotently, so it can
run from a script or cron. See [BUILD.md](BUILD.md). Skip it if you only want workflow #1.

---

## Quickstart (5 minutes)

```bash
# 1. Clone
git clone https://github.com/ceshwar/build-research-wiki.git my-research-wiki
cd my-research-wiki

# 2. Add sources — copy PDFs or Markdown notes into raw/
cp ~/Downloads/some-paper.pdf raw/papers/

# 3. Open the folder in Claude Code (or your LLM agent) and say:
#    "Ingest the new files in raw/."
#    The assistant follows CLAUDE.md and fills wiki/.

# 4. Browse the result
#    Open this folder as a vault in Obsidian → explore the graph + links.
```

That's the whole loop: **add to `raw/` → ask the assistant to ingest → read in Obsidian → ask
questions.**

---

## How it's organized

```
my-research-wiki/
├── CLAUDE.md        # the schema — how the assistant reads, files, and links. Read this.
├── index.md         # catalog of everything in the wiki (the assistant maintains it)
├── log.md           # append-only history of every ingest/query/lint
├── raw/             # YOUR immutable sources — the assistant reads these, never edits them
│   ├── papers/      #   PDFs go here
│   ├── notes/       #   Markdown notes go here
│   └── assets/      #   images / attachments
├── wiki/            # the assistant's output — all generated Markdown
│   ├── sources/     #   one summary page per source
│   ├── entities/    #   people, orgs, tools, venues, datasets
│   ├── concepts/    #   ideas, theories, methods, findings
│   ├── syntheses/   #   cross-cutting analyses + filed answers
│   └── overview.md  #   the evolving big-picture map
└── builder/         # optional deterministic generator (see BUILD.md)
```

The two layers that matter: **`raw/` is the source of truth and is never modified.** **`wiki/`
is everything the assistant writes.** The full rules live in [`CLAUDE.md`](CLAUDE.md).

---

## Make it yours

`CLAUDE.md` is a template. The schema (layers, page formats, linking rules, the
ingest/query/lint operations) works for any research wiki as-is. Tune **§9** to your field —
swap in your domain and the venues/journals you read — and edit the welcome placeholders. The
assistant re-reads this file every session, so changing it changes how your wiki gets built.

---

## Keeping it fresh (optional automation)

The deterministic builder is a plain, idempotent CLI (`python3 builder/build.py`, exit 0 =
healthy), so it drops straight into `cron` / `launchd` / CI for a nightly rebuild:

```cron
# rebuild the portfolio map every night at 3am
0 3 * * *  cd "/path/to/my-research-wiki" && /usr/bin/python3 builder/build.py
```

The LLM-driven ingest (workflow #1) is interactive by design, but you can also script it with
the Claude Agent SDK or a scheduled Claude Code run if you want fully hands-off ingestion.

---

## Requirements

- **An LLM coding agent** for workflow #1 — [Claude Code](https://claude.com/claude-code) is
  the reference, but any agent that can read/write files in a folder works.
- **[Obsidian](https://obsidian.md)** (free) to browse — open this folder as a vault. Optional
  but recommended; everything is plain Markdown so any editor works.
- **Python 3** for the optional builder. PDF text extraction additionally needs
  [`poppler`](https://poppler.freedesktop.org/) (`brew install poppler`).

---

## License

[MIT](LICENSE).
