## Summary
Wire **Enrich next** / **Needs attention** items to actionable steps: open entry path, trigger Deep Dive, or show what is missing per slug.

## Acceptance
- [ ] Each item in **Needs attention** links to `builder/entries/` or `builder/deepdives/` path
- [ ] Optional: in-UI "Run Deep Dive" when Phase 2 LLM lands
- [ ] Counts on dock pills stay in sync after enrich

## Context
- Dive Computer stats: `manager/backend/app/services/vault_manager.py`, `builder/completion.py`
