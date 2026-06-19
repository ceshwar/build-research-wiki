#!/usr/bin/env python3
"""Vault DATA for Research Wiki. Fill these tables, then run builder/build.py.
See builder/README.md for the field reference for each table."""

VAULT = {"name": "Research Wiki", "owner": "", "domain": ""}

# Optional — override default note folders (vault-relative paths).
# NOTES = {"abstracts": "raw/notes/abstracts", "themes": "raw/notes/themes"}
# Use any folder layout you prefer; point P[].note at the file (see below).

# slug -> (display name, core idea, has_source_note)
THEMES = {
    # "example-theme": ("Example Theme", "One-line core idea.", True),
}

# paper dicts: slug, note, title, venue, year, status, pdfs, themes, one, [flag]
#   note — filename in raw/notes/abstracts/ (default), OR any vault-relative path
#          e.g. "raw/notes/lab/2026_chi_example.md"
P = [
    # dict(slug="example", note="2026_venue_example-slug.md", title="Example",
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
