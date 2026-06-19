#!/usr/bin/env python3
"""Vault DATA for Research Wiki. Fill these tables, then run builder/build.py.
See builder/README.md for the field reference for each table."""

VAULT = {"name": "Research Wiki", "owner": "", "domain": ""}

# slug -> (display name, core idea, has_source_note)
THEMES = {
    # "example-theme": ("Example Theme", "One-line core idea.", True),
}

# paper dicts: slug, note (abstract-note filename), title, venue, year,
# status ("mapped"|"no-pdf"|"inferred"), pdfs [..], themes [..], one (one-liner), [flag]
P = [
    # dict(slug="example", note="(2026_VENUE) Example.md", title="Example",
    #      venue="VENUE", year=2026, status="mapped", pdfs=["example.pdf"],
    #      themes=["example-theme"], one="One-line contribution."),
]

# slug -> short display title (link aliases in concept/entity pages)
TITLES = {}

# slug -> (name, definition, [paper slugs])
CONCEPTS = {}
# slug -> (name, role, definition, [paper slugs])
PEOPLE = {}
# slug -> (name, kind, definition, [paper slugs])
PLATFORMS = {}
METHODS = {}
