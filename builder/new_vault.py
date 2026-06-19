#!/usr/bin/env python3
"""Scaffold a NEW LLM-Wiki vault (different corpus, same machinery) from this one.

    python3 builder/new_vault.py /path/to/NewVault "Vault Name"

Creates the folder skeleton, copies the engine (build.py, engine_*.py, extract_pdfs.py,
README), and writes a STARTER data.py + empty nav files. It does NOT copy this vault's
papers, notes, or deep dives — you supply those. Then:
  1) drop PDFs in  <new>/raw/papers/  and abstract notes in
     <new>/raw/notes/recent project abstracts/  (+ theme notes in research themes/)
  2) fill in  <new>/builder/data.py  (THEMES, P, then CONCEPTS/PEOPLE/... after deep dives)
  3) python3 <new>/builder/build.py
"""
import os, sys, shutil

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_FILES = ["build.py", "engine_papers.py", "engine_web.py", "extract_pdfs.py", "new_vault.py", "README.md"]

STARTER_DATA = '''#!/usr/bin/env python3
"""Vault DATA for {name}. Fill these tables, then run builder/build.py.
See builder/README.md for the field reference for each table."""

VAULT = {{"name": "{name}", "owner": "", "domain": ""}}

# slug -> (display name, core idea, has_source_note)
THEMES = {{
    # "example-theme": ("Example Theme", "One-line core idea.", True),
}}

# paper dicts: slug, note (abstract-note filename), title, venue, year,
# status ("mapped"|"no-pdf"|"inferred"), pdfs [..], themes [..], one (one-liner), [flag]
P = [
    # dict(slug="example", note="(2026_VENUE) Example.md", title="Example",
    #      venue="VENUE", year=2026, status="mapped", pdfs=["example.pdf"],
    #      themes=["example-theme"], one="One-line contribution."),
]

# slug -> short display title (link aliases in concept/entity pages)
TITLES = {{}}

# slug -> (name, definition, [paper slugs])
CONCEPTS = {{}}
# slug -> (name, role, definition, [paper slugs])
PEOPLE = {{}}
# slug -> (name, kind, definition, [paper slugs])
PLATFORMS = {{}}
METHODS = {{}}
'''

DIRS = ["raw/papers", "raw/assets", "raw/notes/recent project abstracts", "raw/notes/research themes",
        "wiki/papers", "wiki/themes", "wiki/concepts", "wiki/entities", "wiki/syntheses", "wiki/sources",
        "builder/deepdives", "builder/cache"]


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3 builder/new_vault.py /path/to/NewVault [\"Vault Name\"]")
    dest = os.path.abspath(sys.argv[1])
    name = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(dest)
    if os.path.exists(dest) and os.listdir(dest):
        sys.exit(f"refusing: {dest} exists and is non-empty.")
    for d in DIRS:
        os.makedirs(os.path.join(dest, d), exist_ok=True)
        if d.startswith(("raw/", "wiki/")):
            open(os.path.join(dest, d, ".gitkeep"), "a").close()
    for fn in ENGINE_FILES:
        src = os.path.join(BUILDER_DIR, fn)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dest, "builder", fn))
    with open(os.path.join(dest, "builder", "data.py"), "w") as f:
        f.write(STARTER_DATA.format(name=name))
    # nav + gitignore stubs
    open(os.path.join(dest, "index.md"), "w").write(f"# Index\n\n*(empty — run builder/build.py)*\n")
    open(os.path.join(dest, "log.md"), "w").write(f"# Log\n\n## [setup] {name} scaffolded with builder/new_vault.py.\n")
    open(os.path.join(dest, "wiki", "overview.md"), "w").write(f"# {name} — Overview\n\n*(hand-maintained)*\n")
    open(os.path.join(dest, ".gitignore"), "w").write("builder/cache/\nbuilder/__pycache__/\n.DS_Store\n")
    print(f"Scaffolded '{name}' at {dest}")
    print("Next: add sources to raw/, fill builder/data.py, then  python3 builder/build.py")


if __name__ == "__main__":
    main()
