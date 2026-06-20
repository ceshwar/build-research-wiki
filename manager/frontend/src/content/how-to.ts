/** In-app guide — distilled from docs/SCUBA-IDEAVERSE.md and docs/GETTING-STARTED.md */

export const HOW_TO_SECTIONS = [
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
      '**Shallow reef** — a low-stakes trial reef with demo papers in `examples/minimal-vault`. Learn the UI here; nothing you break matters. (Like a training dive in shallow water.)',
      '**Blank reef** — the repo-root scaffold (`CLAUDE.md`, empty `raw/`, starter `builder/`). Copy it or run `python3 builder/new_vault.py` to spawn your own lab reef.',
      '**Connect your reef** — in the reef menu, choose *+ Connect your reef…* to point SCUBA at an Obsidian folder already on your machine. Saved locally (not in git). This wires up *your* reef — not the same as Blank reef.',
    ],
  },
  {
    id: 'terms',
    title: 'SCUBA terms',
    terms: [
      { name: 'Reef', desc: 'Your research wiki — an Obsidian folder SCUBA charts and connects.' },
      { name: 'Dock', desc: 'A channel with its own folder under `raw/` (e.g. ⚓ My Portfolio → `raw/papers/`). Hover a dock pill for its purpose.' },
      { name: 'Quick Dip', desc: 'Tier 1 charting: PDF title, abstract, venue, year onto the wiki — no guessing.' },
      { name: 'Deep Dive', desc: 'Tier 2 enrichment: themes, one-liners, analysis in `builder/deepdives/`.' },
      { name: 'Chart', desc: 'Generated wiki pages under `wiki/papers/` or `wiki/sources/`.' },
      { name: 'Chart status', desc: 'Per-dock charting tracker — on chart, awaiting chart, quick dip, enrich next.' },
      { name: 'Map', desc: 'Charted items for the active dock — **List** table or **By theme** (portfolio). Expand **Note** for one-liner + PDF.' },
      { name: 'Workspace', desc: 'Focused view: `/ Reef › Dock` path + tabs (Map · Chart status · Actions). **/** switches reefs; reef name picks a dock.' },
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
      { name: 'Enrich next', desc: 'Themes/abstract present but deep dive sections missing.' },
      { name: 'Deep dive 📄', desc: 'Fully enriched — refine in Obsidian if needed.' },
    ],
  },
  {
    id: 'more',
    title: 'More documentation',
    links: [
      { label: 'SCUBA Ideaverse (full)', href: 'https://github.com/ceshwar/build-research-wiki/blob/main/docs/SCUBA-IDEAVERSE.md' },
      { label: 'Getting started', href: 'https://github.com/ceshwar/build-research-wiki/blob/main/docs/GETTING-STARTED.md' },
      { label: 'CLAUDE.md schema', href: 'https://github.com/ceshwar/build-research-wiki/blob/main/CLAUDE.md' },
    ],
  },
] as const
