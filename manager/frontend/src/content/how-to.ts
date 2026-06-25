/** In-app guide — distilled from docs/PORTOLAN.md and docs/GETTING-STARTED.md */

export const HOW_TO_SECTIONS = [
  {
    id: 'about',
    title: 'What is Portolan',
    body: [
      'A **portolan** is a navigational chart — the old sailor’s map of coastlines and harbors, drawn to keep you oriented at sea. Portolan does the same for your field: it **reads the papers you dock and charts how they connect**, so you stay oriented as the literature keeps rising instead of losing the thread.',
      '**The gap it fills:** tools help you write and store — Zotero stores, Obsidian links — but almost nothing helps you **read**. Portolan’s verb is **reads**: it turns a pile of PDFs into a compounding, browsable chart you own as plain Markdown, versioned with git.',
      '**What you do:** dock papers → **Quick Dip** charts the facts → **Deep Dive** enriches (themes, findings, connections) → **Navigate** the graph → open it all in Obsidian.',
      'Built for **research papers** — the same dock → chart → enrich loop works for any corpus you need to actually read.',
    ],
  },
  {
    id: 'start',
    title: 'Quick start',
    body: [
      'Pick a **reef** — click **/** in the path bar, or start on **Shallow reef**.',
      'Choose a **dock** — click the reef name in the path (`/ Shallow reef › …`).',
      'Use **Get ingest prompt** in Actions for Deep Dive enrichment with your coding agent.',
      'Open **Obsidian** (purple icon) to browse the wiki chart.',
    ],
  },
  {
    id: 'reefs',
    title: 'The three kinds of reef',
    body: [
      '**Shallow reef** — a low-stakes trial reef with demo papers in `examples/minimal-vault`. Learn the UI here; nothing you break matters.',
      '**Blank reef** — the repo-root scaffold (`CLAUDE.md`, empty `raw/`, starter `builder/`). Copy it or run `python3 builder/new_vault.py` to spawn your own lab reef.',
      '**Connect your reef** — in the reef menu, choose *+ Connect your reef…* to point Portolan at an Obsidian folder already on your machine. Saved locally (not in git).',
    ],
  },
  {
    id: 'terms',
    title: 'Key terms',
    terms: [
      { name: 'Reef', desc: 'Your research wiki — an Obsidian folder Portolan charts and connects.' },
      { name: 'Dock', desc: 'A channel with its own folder under `raw/` (e.g. ⚓ My Portfolio → `raw/papers/`). Hover a dock pill for its purpose.' },
      { name: 'Quick Dip', desc: 'Tier 1 charting: PDF title, abstract, venue, year onto the wiki — no guessing.' },
      { name: 'Deep Dive', desc: 'Tier 2 enrichment via **qwen3:32b** (Ollama): themes, one-liners, analysis in `builder/deepdives/`. Content-complete ≠ accurate — see **Needs review**.' },
      { name: 'Needs review', desc: 'LLM-filled Deep Dive awaiting human or frontier-model verification. Shown with ⚠ until you **Mark verified**.' },
      { name: 'Human verified', desc: 'A reviewer confirmed claims on a processed paper. Stored in `builder/verification.json` + wiki frontmatter.' },
      { name: 'Chart', desc: 'Generated wiki pages under `wiki/papers/` or `wiki/sources/` — the compounding knowledge base you browse.' },
      { name: 'Status', desc: 'Per-dock pipeline tracker — on chart, awaiting chart, quick dip, enrich next.' },
      {
        name: 'Navigate',
        desc: 'Browse charted items for the active dock — **List** table, **By theme** (portfolio clusters), or **Graph** (wikilink network). On Graph, toggle **Show** layers (default: papers, themes, concepts); hover highlights in orange. Expand **Note** for one-liner + PDF. Toggle **Edit** (List only) to remove papers from the chart.',
      },
      {
        name: 'Graph edges',
        desc: 'The graph starts from charted papers and follows `[[wikilinks]]` in wiki pages. You will see paper→theme and paper→concept links, plus cross-links when pages link to each other (e.g. theme→theme). Concept→concept links appear only if your concept pages link to each other.',
      },
      { name: 'Workspace', desc: 'Focused view: `/ Reef › Dock` path + tabs (Navigate · Status · Actions). **/** switches reefs; reef name picks a dock.' },
      { name: 'Update chart', desc: 'Runs Quick Dip + rebuild for new docked files.' },
      { name: 'Full rebuild', desc: 'Regenerates the entire wiki from builder entries.' },
    ],
  },
  {
    id: 'pipeline',
    title: 'Pipeline',
    body: [
      '**Dock PDF** → lands in `raw/` (immutable)',
      '**Quick Dip** → `builder/entries/` + `wiki/papers/` facts from the PDF',
      '**Deep Dive** → themes, one-liner, `builder/deepdives/` (your agent or by hand)',
      '**On chart** → fully enriched paper page in Obsidian',
    ],
  },
  {
    id: 'status',
    title: 'Completion states',
    terms: [
      { name: 'Awaiting chart', desc: 'File docked in `raw/` but not mapped yet — run Update chart.' },
      { name: 'Quick dip 🤿', desc: 'On chart with PDF facts only — needs Deep Dive.' },
      { name: 'Scaffolded', desc: 'On chart from data.py but the entry file is still thin — missing themes, abstract, or one-liner. Not an error; needs Deep Dive.' },
      { name: 'Enrich next', desc: 'Themes/abstract present but deep dive sections missing.' },
      { name: 'Deep dive 📄', desc: 'Fully enriched — refine in Obsidian if needed.' },
    ],
  },
  {
    id: 'more',
    title: 'More documentation',
    links: [
      { label: 'Portolan (full guide)', href: 'https://github.com/ceshwar/build-research-wiki/blob/main/docs/PORTOLAN.md' },
      { label: 'Getting started', href: 'https://github.com/ceshwar/build-research-wiki/blob/main/docs/GETTING-STARTED.md' },
      { label: 'CLAUDE.md schema', href: 'https://github.com/ceshwar/build-research-wiki/blob/main/CLAUDE.md' },
    ],
  },
] as const
