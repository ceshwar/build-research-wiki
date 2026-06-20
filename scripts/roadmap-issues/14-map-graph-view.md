## Summary
In-app **Graph** tab on portfolio dock Map views — force-directed wikilink graph (papers, themes, concepts, entities, syntheses) built from vault wiki files, without embedding Obsidian’s graph view.

## Shipped (v0.4.6)
- [x] `builder/chart_graph.py` — wikilink closure from charted papers + theme edges
- [x] `GET /chart-graph?vault_id&channel_id` API
- [x] Map tab: **List · By theme · Graph** (portfolio docks only)
- [x] `react-force-graph-2d` canvas; click node → Obsidian (until #14 in-app viewer)
- [x] Status filters on Graph; type legend; tests in `tests/test_chart_graph.py`

## Follow-ups
- [ ] In-app node preview (#14) instead of Obsidian-only click
- [ ] Layer toggles (hide concepts / entities)
- [ ] Search + focus node
- [ ] 2-hop option for large reefs
- [ ] Ingest-dock subgraph (sources)

## Context
- Obsidian graph cannot be embedded — this is an Ideaverse-native graph from the same `wiki/` files.
- Related: GitHub #14 in-app viewer, #15 map graph (shipped)
