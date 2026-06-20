## Summary
Render reef content **inside SCUBA Ideaverse** instead of relying solely on Obsidian deep links. Users choose where to open papers, notes, PDFs, and theme pages: **in-app** or **Obsidian**.

## Problem
Today map links use `obsidian://` URIs. That fails when:
- The reef folder is not registered in Obsidian (e.g. sandbox copies like `examples/local-reef`).
- Obsidian is not installed or not running.
- Users want a quick preview without context-switching.

v0.4.5 mitigates this with Obsidian vault auto-detection and optional `obsidian_vault_id` overrides in `vaults.user.yaml` — still Obsidian-only.

## Proposal
- **In-app viewer** for markdown wiki pages (`wiki/papers/`, `wiki/themes/`, `wiki/sources/`) and optional PDF preview.
- **Per-reef or global preference**: `view_in` = `app` | `obsidian` | `ask` (default TBD).
- Map / Chart status links respect the preference; Obsidian remains available as explicit fallback (“Open in Obsidian”).
- Backend serves file content from vault path (read-only; never modify `raw/`).

## Acceptance
- [ ] Settings or reef config: choose default viewer (app vs Obsidian)
- [ ] Clicking a paper title opens an in-app panel or route with rendered markdown (frontmatter stripped or shown)
- [ ] PDFs: inline viewer or download; at minimum open via system default when in-app PDF is deferred
- [ ] “Open in Obsidian” action still available when vault is registered
- [ ] Sandbox reefs work without Obsidian registration when `view_in: app`
- [ ] Document preference in `manager/README.md` and reef connect flow

## Context
- Current links: `manager/frontend/src/App.tsx` (`ReefLink`, `obsidianReefHref`)
- Obsidian registration: `manager/backend/app/services/vault_manager.py` (`_obsidian_link_meta`)
- Related: #3 Enrich actions, reef profiles (#11)
