/** In-app guide — distilled from docs/PORTOLAN.md and docs/GETTING-STARTED.md */

export const HOW_TO_SECTIONS = [
  {
    id: 'about',
    title: 'What is Portolan',
    body: [
      'A **portolan** is a navigational chart — the old sailor’s map of coastlines and harbors, drawn to keep you oriented at sea. Portolan does the same for your field: it **reads the papers you dock and charts how they connect**, so you stay oriented as the literature keeps rising instead of losing the thread.',
      '**The gap it fills:** tools help you write and store — Zotero stores, Obsidian links — but almost nothing helps you **read**. Portolan’s verb is **reads**: it turns a pile of PDFs into a compounding, browsable chart you own as plain Markdown, versioned with git.',
      '**What you do:** dock papers → **Update chart** (metadata / Uncharted) → **Quick Dip** (LLM) → review → **Deep dive** (verified) → **Navigate** and **Query**.',
      'Built for **research papers** — the same dock → chart → enrich loop works for any corpus you need to actually read.',
    ],
  },
  {
    id: 'start',
    title: 'Quick start',
    body: [
      'Pick a **reef** — click **/** in the path bar, or start on **Shallow reef**.',
      'Choose a **dock** — click the reef name in the path (`/ Shallow reef › …`).',
      '**Update chart** surfaces docked PDFs; **Run Quick Dip (LLM)** when Ollama is available.',
      'Open papers in-app or in Obsidian from Navigate links.',
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
      { name: 'Uncharted ◎', desc: 'On chart but not LLM-ingested yet — mild red pill. PDF/metadata only until Quick Dip runs.' },
      { name: 'Quick dip 🤿', desc: 'LLM-ingested content awaiting human review — green pill. Shown in Quick dip filter until verified.' },
      { name: 'Deep dive 🦑', desc: 'Verified gold-standard paper — gold pill. Best source for Query scope.' },
      { name: 'Chart', desc: 'Generated wiki pages under `wiki/papers/` or `wiki/sources/` — the compounding knowledge base you browse.' },
      { name: 'Status', desc: 'Per-dock pipeline: on chart, awaiting chart, uncharted, quick dip, deep dive.' },
      {
        name: 'Navigate',
        desc: 'Browse charted items — **List** table, **By theme** (portfolio clusters), or **Graph**. Filters: All · Deep dive · Quick dip · Uncharted.',
      },
      { name: 'Workspace', desc: 'Focused view: `/ Reef › Dock` path + tabs (Navigate · Query · Status · Actions).' },
      { name: 'Update chart', desc: 'Maps new docked PDFs onto the chart (Uncharted metadata). Run Quick Dip separately when LLM is ready.' },
      { name: 'Full rebuild', desc: 'Regenerates the entire wiki from builder entries.' },
    ],
  },
  {
    id: 'pipeline',
    title: 'Pipeline',
    body: [
      '**Dock PDF** → lands in `raw/` (immutable)',
      '**Update chart** → metadata on chart (**Uncharted**)',
      '**Quick Dip (LLM)** → themes, one-liner, analysis in `builder/deepdives/`',
      '**Review** → mark verified → **Deep dive**',
    ],
  },
  {
    id: 'status',
    title: 'Trust tiers',
    terms: [
      { name: 'Awaiting chart', desc: 'File docked in `raw/` but not mapped yet — run Update chart.' },
      { name: 'Uncharted ◎', desc: 'On chart, not LLM-ingested — run Quick Dip when Ollama is available.' },
      { name: 'Quick dip 🤿', desc: 'LLM-filled — needs your review before Deep dive.' },
      { name: 'Deep dive 🦑', desc: 'Verified — safe to cite in Query “Deep dive” scope.' },
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
