# CLAUDE.md — Research Wiki Operating Manual

> **Portability:** This file is the canonical schema. [`AGENTS.md`](AGENTS.md) points here for OpenAI Codex, OpenCode, and other agents that expect that filename. The instructions are AI-agnostic.

This vault is an **LLM Wiki**: a persistent, compounding knowledge base that an LLM
assistant (e.g. Claude) builds and maintains on your behalf. You curate sources, explore,
and ask questions. The assistant does the reading, summarizing, cross-referencing, filing,
and bookkeeping.

This file is the schema. It is the single source of truth for how the wiki is structured
and how the assistant operates on it. The assistant reads it at the start of every session.
You and the assistant co-evolve it over time — when you discover a better convention, update
this file.

> **Make it yours.** This is a template. Replace the bracketed placeholders below
> (`<your domain>`, etc.) and tune §9 to your field. The schema in §1–§8 works for any
> research/academic wiki as-is.

---

## 1. The three layers

1. **Raw sources** (`raw/`) — Your curated source documents: articles, papers, notes,
   transcripts, images, data files. **These are immutable. The assistant reads from them but
   NEVER modifies, renames, or deletes them.** This is the source of truth.

2. **The wiki** (`wiki/`) — The assistant's output. Markdown pages it creates and maintains:
   source summaries, entity pages, concept pages, syntheses. **The assistant owns this layer.**

3. **The schema** (this file) — How everything is structured and how the assistant works.

Plus two navigation files at the root: `index.md` (content catalog) and `log.md`
(chronological record).

---

## 2. Directory structure

```
research-wiki/
├── CLAUDE.md             # this file — the schema
├── index.md             # content catalog (what exists, organized by category)
├── log.md               # append-only chronological record of all operations
├── raw/                 # immutable sources (never edited)
│   └── assets/          # downloaded images / attachments
└── wiki/                # everything the assistant writes
    ├── sources/         # one summary page per ingested source
    ├── entities/        # people, orgs, tools, products, places — proper nouns
    ├── concepts/        # ideas, topics, theories, methods, frameworks
    ├── syntheses/       # cross-cutting analyses, comparisons, theses, answers
    └── overview.md      # the evolving big-picture map of the whole vault
```

If a new category is genuinely needed, propose it first, then add it here before using it.
Don't silently invent folders.

---

## 3. Naming conventions

- **Files:** `kebab-case.md`. Lowercase, hyphens, no spaces. Example:
  `wiki/concepts/incremental-knowledge-compilation.md`.
- **Page title:** an H1 (`# Human Readable Title`) at the top of every page.
- **Source files** in `wiki/sources/` are named after the source, prefixed with the ingest
  date for sortability: `2026-06-19-some-source.md`.
- **Entity/concept pages** are named for the thing itself: `wiki/entities/obsidian.md`,
  `wiki/concepts/memex.md`. One page per distinct thing. Use the singular.
- Avoid duplicates. Before creating a page, check the index and the relevant folder for an
  existing page on the same thing. **Update the existing page rather than forking it.**

---

## 4. Page format & frontmatter

Every wiki page starts with YAML frontmatter, then an H1, then the body. Frontmatter powers
Obsidian's Dataview and lets the assistant query the vault.

### Source page (`wiki/sources/`)

```markdown
---
type: source
title: <human title of the source>
source_file: raw/<the original file>      # link back to the immutable source
author: <if known>
source_type: article | paper | book | transcript | note | video | webpage | dataset
date_published: <YYYY-MM-DD or unknown>
date_ingested: YYYY-MM-DD
tags: [topic-a, topic-b]
status: ingested
---

# <Title>

> One-sentence what-this-is.

## Summary
3–8 paragraph faithful summary of the source's content.

## Key takeaways
- Bullet points. The claims worth remembering.

## Entities & concepts
Links to every entity/concept page this source touches: [[obsidian]], [[memex]], ...

## Notable claims / data
Specific facts, numbers, quotes worth citing later. Flag anything that contradicts other
sources with **⚠ contradicts [[other-page]]:** ...

## My notes
(Reserved for your own annotations. The assistant leaves this for you unless asked.)
```

### Academic paper — extra fields (`source_type: paper`)

When the source is a paper, extend the source frontmatter and add the research-specific
sections below:

```markdown
---
type: source
source_type: paper
title: <paper title>
source_file: raw/<file.pdf or .md>
authors: [Last F., Last F.]
venue: <CHI | CSCW | ICWSM | NeurIPS | arXiv | journal name>
year: <YYYY>
doi_or_url: <if known>
citation: "<one-line formatted citation>"
date_ingested: YYYY-MM-DD
tags: [...]
status: ingested
---
```
Plus these sections, in addition to Summary / Key takeaways / Entities & concepts:
- **## Research question** — what the paper asks.
- **## Method** — data, study design, sample, analysis. Enough to judge the evidence.
- **## Findings** — the actual results, with effect sizes/numbers where given.
- **## Claims & evidence** — each major claim paired with the evidence behind it, so the
  synthesis can weight claims by strength. Flag contradictions with **⚠ contradicts [[x]]**.
- **## Limitations & threats** — what the authors (and the assistant) note as caveats.
- **## Relevance to my work** — connection to your research threads (left light unless known).

### Entity / concept page (`wiki/entities/`, `wiki/concepts/`)

```markdown
---
type: entity | concept
title: <name>
aliases: [other names it's called]
tags: [...]
sources: [2026-06-19-some-source]          # source slugs that mention this
updated: YYYY-MM-DD
---

# <Name>

> One-sentence definition.

## Overview
The synthesized understanding, compiled from ALL sources — not a single source's view.

## Connections
How this relates to other pages: [[...]]. Why the link matters, not just a bare link.

## Open questions / contradictions
What's unresolved, what sources disagree on.

## Sources
- [[2026-06-19-some-source]] — what this source contributed about this entity.
```

### Synthesis page (`wiki/syntheses/`)

Free-form, but always: frontmatter (`type: synthesis`), an H1, a clear thesis or question
at the top, body with inline `[[links]]` and citations, and a Sources section. **Filed
answers go here** (see §6, Query).

---

## 5. Linking & citation rules

- **Link liberally.** Use Obsidian wikilinks `[[page-name]]` (match the file slug without
  `.md`). Every proper noun or concept that has — or should have — its own page gets linked.
- A `[[link]]` to a page that doesn't exist yet is fine — it's a "red link" marking a page
  worth creating later. The lint pass (§6) surfaces these.
- **Every claim in a synthesis or summary traces to a source.** Cite as `[[source-slug]]`.
  Never assert something as known from the wiki without a source behind it. If the assistant
  brings in outside/web knowledge, it labels it explicitly as **[external]** so it's
  distinguishable from what the curated sources actually say.
- Bidirectional thinking: when source A adds info to entity X, both the source page and X's
  page should reference each other.

---

## 6. The three operations

### INGEST — adding sources
Trigger: you drop one or more files in `raw/` and say to process them.

**Default mode: BATCH with light supervision.** Process all pending sources in one pass
without stopping to confirm each, then deliver a single digest at the end. Don't stop
mid-batch to discuss takeaways unless something genuinely needs a decision (e.g. a hard
contradiction that changes a thesis). You review the result in Obsidian after.

For each source in the batch:
1. **Read** it fully from `raw/`. For images: read the text first, then view referenced
   images separately. For PDFs: use the pdf skill / read pages as needed.
2. **Write the source page** in `wiki/sources/` (date-prefixed slug; use the §4 paper format
   when `source_type: paper`).
3. **Propagate** across the wiki — the part that makes it compound:
   - Update or create every relevant entity and concept page.
   - Integrate new info into existing `## Overview` sections; don't just append.
   - **Flag contradictions** with **⚠ contradicts [[x]]** — for papers, weigh by evidence
     strength (sample size, method, replication), don't just note disagreement.
   - Add/update cross-references in both directions.
   - Update `wiki/overview.md` if the big picture shifted.
   A single source typically touches 8–15 pages.

Then once per batch:
4. **Update `index.md`** — all new sources and pages, with one-line summaries; bump totals.
5. **Append to `log.md`** — one `ingest` entry per source (or one batch entry listing each).
6. **Deliver a digest**: a table of sources ingested, the new/updated pages, every
   contradiction surfaced, new red links worth creating, and 2–5 follow-up questions or
   sources worth chasing. This digest is your review surface — make it scannable.

### QUERY — asking questions
Trigger: you ask a question of the wiki.

1. **Read `index.md` first** to find relevant pages, then drill into them. (At larger scale,
   fall back to grep/search over `wiki/`.)
2. Synthesize an answer **with `[[citations]]`** to the pages/sources it came from.
3. Choose the output form that fits: prose, a comparison table, a chart, a slide deck.
4. **Offer to file good answers back into the wiki** as a `wiki/syntheses/` page. Explorations
   should compound, not vanish into chat. If filed, update index + log.

### LINT — health-checking the wiki
Trigger: you ask for a lint / health check (do periodically).

Scan for and report (don't auto-fix unless told):
- **Contradictions** between pages.
- **Stale claims** superseded by newer sources.
- **Orphan pages** — no inbound links.
- **Red links / missing pages** — concepts referenced but lacking their own page.
- **Missing cross-references** — pages that should link but don't.
- **Data gaps** — open questions a web search or new source could fill.
- Suggest **new questions to investigate** and **new sources to find**.

---

## 7. index.md and log.md

**`index.md`** is content-oriented — a catalog of everything, organized by category (Sources,
Entities, Concepts, Syntheses), each line: `[[page]] — one-line summary`. Updated on every
ingest and every filed synthesis. Read first on every query.

**`log.md`** is chronological and append-only. Every entry starts with a consistent, greppable
prefix so `grep "^## \[" log.md | tail -5` gives the recent history:

```
## [YYYY-MM-DD] <ingest|query|lint|synthesis> | <short label>
- what happened, pages touched, contradictions found, follow-ups.
```

Never rewrite past log entries; only append.

---

## 8. Operating principles

- **The assistant writes the wiki; you do not.** You curate, explore, ask. The assistant does
  the grunt work — summarizing, cross-referencing, filing, bookkeeping.
- **Faithful, not embellished.** Summaries reflect the source. The assistant doesn't invent
  facts. Outside knowledge is labeled **[external]**.
- **Compile once, keep current.** New sources update the synthesis in place; don't re-derive
  from scratch. Contradictions are flagged, not silently overwritten.
- **Touch many files per pass.** Maintenance cost is near zero for the assistant — that's the
  whole point. Don't skip cross-reference updates because they're tedious.
- **Optimize for Obsidian.** Real wikilinks, no orphans, meaningful connections — so graph
  view and link-following work.
- **Batch by default.** Process all pending sources in one pass and deliver a digest; don't
  stop to confirm each unless a decision genuinely requires it.
- **Report changes plainly.** After every operation, say exactly what was created/changed.

---

## 9. Domain: research / academic

This template assumes a **research/academic** domain. Tune this section to your field
(replace `<your domain>` and the example venues with your own).

- **Papers are first-class sources.** Use `source_type: paper` and the richer paper format in
  §4 (research question, method, findings, claims & evidence, limitations).
- **Weigh claims by evidence.** When syntheses draw on papers, prefer well-supported claims
  and note method/sample caveats. A contradiction between a large study and a small one is not
  a tie — say so.
- **Build a literature web.** Entity pages for **authors, venues, datasets, methods**; concept
  pages for **theories, constructs, and findings**. Track who-cites-what and where threads
  converge or conflict — this is the comparative advantage over reading PDFs alone.
- **Evolving thesis.** `wiki/overview.md` should track the open research questions and the
  current state of the synthesis on each active thread, updated as papers accumulate.
- **Useful output forms for queries:** comparison tables (methods/findings across papers),
  literature-gap analyses, and `wiki/syntheses/` pages that read like mini related-work
  sections. These are the high-value artifacts to file back.

---

## 10. Optional: the deterministic portfolio-map builder

Beyond the LLM-driven ingest above, this repo ships an **optional deterministic builder**
(`builder/`) for one specific high-value pattern: a **structure map of a research portfolio** —
a set of papers organized by research theme, with the cross-cutting threads between them. It
regenerates a slice of the wiki from a single data file, idempotently, so it can run from a
script or cron. Skip this whole section if you only want the LLM-driven workflow.

### Source layout (`raw/`)
- `raw/papers/` — the paper PDFs (immutable). Identity comes from the PDF's own title (use
  `mdls -name kMDItemTitle` or `pdftotext -f 1 -l 1`), not the filename.
- `raw/notes/` — **your curated Markdown notes** (immutable). Organize subfolders however you
  like (`abstracts/`, `themes/`, `lab-meetings/`, …). The builder does not assume a fixed tree —
  it reads paths from `builder/data.py`.
- **Suggested defaults** (what `new_vault.py` scaffolds):
  - `raw/notes/abstracts/` — one note per paper, named `{year}_{venue}_{slug}.md` (lowercase,
    underscores, no spaces), with **`[[theme-slug]]` wikilinks on line 1** then `## Abstract:`.
    This is the **authoritative paper→theme mapping** (author-written; treat as ground truth).
  - `raw/notes/themes/` — one note per theme, named `{theme-slug}.md`, with a `**Core idea:**`
    one-liner (display title lives in `data.py` / the wiki, not the filename).
- If a PDF has no abstract note, draft one in your chosen folder using the same format (lead with
  an HTML comment marking it assistant-drafted + themes inferred), then flag for confirmation.

### Wiki layout (added by the builder)
- `wiki/themes/<slug>.md` — `type: theme` hub pages: core idea, the papers under it, related
  themes (by co-occurrence). One per theme.
- `wiki/papers/<slug>.md` — `type: paper` pages: title, venue, year, `status`
  (`mapped`/`no-pdf`/`inferred`), theme links, the abstract/notes, and a **Deep dive**
  placeholder for Phase 2. Slugs are short titles (e.g. `slm-mod.md`), not date-prefixed.
- `wiki/overview.md` — the portfolio map: theme landscape + **cross-cutting threads** +
  platforms/methods + pending confirmations.
- `index.md` — catalog: themes by size, papers by year, with status icons (📄/📝/🔎).

### How it's generated & maintained
- All generator code lives in **`builder/`** — see [BUILD.md](BUILD.md) and
  [builder/README.md](builder/README.md). One entrypoint: `python3 builder/build.py`
  (idempotent, portable — auto-detects its vault; ends with a red-link check).
- **Engine vs data:** `builder/build.py` + `builder/engine_papers.py` + `builder/engine_web.py`
  are generic; **`builder/data.py`** holds your corpus (THEMES, P, CONCEPTS, PEOPLE, …) and is
  the only file you edit for new papers.
- Paper **Deep dive** sections live in `builder/deepdives/<slug>.md` (source of truth, injected
  at build — edit there, not in the paper page). `builder/cache/` is disposable PDF-text cache
  (`builder/extract_pdfs.py`, needs `poppler`). `overview.md`, `wiki/syntheses/`, `log.md` are
  hand-maintained.
- **New vault from a different corpus:** `python3 builder/new_vault.py /path/to/NewVault "Name"`
  scaffolds a fresh vault with a copy of the engine + a starter `data.py`.
- **Two-phase ingest:** Phase 1 = this map (from abstracts + first-page PDF checks). Phase 2 =
  per-paper deep dives (full method/findings/claims/limitations from full PDFs), thread by
  thread, filling each paper's Deep dive section. Author/venue/dataset **entity** pages (§9's
  literature web) are deferred to Phase 2.
- When a new paper arrives: add/confirm its abstract note (any path under `raw/notes/` —
  register in `builder/data.py`), add a row to the generator's data table, re-run, then update
  `overview.md` threads + `log.md`.
