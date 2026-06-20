#!/usr/bin/env python3
"""Scaffold a NEW LLM-Wiki vault (different corpus, same machinery) from this one.

    python3 builder/new_vault.py /path/to/NewVault "Vault Name"

Creates the folder skeleton, copies the engine, entry templates, and writes a STARTER
data.py. Uploads go to raw/ only; chart entries land in builder/entries/ after Surface Interval.

Then:
  1) dock files in raw/papers/ (and other channel folders)
  2) python3 builder/map_channel.py --channel my-portfolio
  3) python3 builder/build.py
  4) edit builder/entries/<channel>/<slug>.md — copy from builder/templates/ to start by hand
"""
import os
import shutil
import sys

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_FILES = [
    "build.py", "engine_papers.py", "engine_web.py", "engine_ingest.py",
    "map_channel.py", "map_pdfs.py", "templates_util.py", "completion.py",
    "quick_dip.py", "qa_quick_dip.py", "docks_util.py", "channel_status.py", "extract_pdfs.py",
    "new_vault.py", "README.md",
]

STARTER_DATA = '''#!/usr/bin/env python3
"""Vault DATA for {name}. Fill these tables, then run builder/build.py.
See builder/README.md for the field reference for each table."""

VAULT = {{"name": "{name}", "owner": "", "domain": ""}}

# Optional — legacy raw note folders (hand-curated corpus only).
# NOTES = {{"abstracts": "raw/notes/abstracts", "themes": "raw/notes/themes",
#           "entries": "builder/entries"}}

# slug -> (display name, core idea, has_source_note)
THEMES = {{
    # "example-theme": ("Example Theme", "One-line core idea.", True),
}}

# paper dicts: slug, entry (builder/entries/...), title, venue, year, status, pdfs, themes, one, [flag]
#   entry — vault-relative path to chart entry in builder/entries/<channel>/<slug>.md
P = [
    # dict(slug="example", entry="builder/entries/my-portfolio/example.md",
    #      note="builder/entries/my-portfolio/example.md", title="Example",
    #      venue="VENUE", year=2026, status="mapped", pdfs=["example.pdf"],
    #      themes=["example-theme"], one="One-line contribution."),
]

# ingest-channel artifacts (optional; auto_sources.json is created by map_channel.py)
S = []

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

DIRS = [
    "raw/papers", "raw/literature", "raw/dive-log",
    "raw/notes/inbox", "raw/assets",
    "builder/entries/my-portfolio", "builder/entries/lit-review",
    "builder/entries/dive-log", "builder/entries/ideas",
    "builder/deepdives", "builder/cache",
    "wiki/papers", "wiki/themes", "wiki/concepts", "wiki/entities",
    "wiki/syntheses", "wiki/sources",
]

CHANNEL_TEMPLATE_DIRS = [
    "my-portfolio", "lit-review", "ideas",
]


def _copy_tree(src, dest):
    if not os.path.isdir(src):
        return
    os.makedirs(dest, exist_ok=True)
    for name in os.listdir(src):
        s = os.path.join(src, name)
        d = os.path.join(dest, name)
        if os.path.isdir(s):
            _copy_tree(s, d)
        else:
            shutil.copy2(s, d)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3 builder/new_vault.py /path/to/NewVault [\"Vault Name\"]")
    dest = os.path.abspath(sys.argv[1])
    name = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(dest)
    if os.path.exists(dest) and os.listdir(dest):
        sys.exit("refusing: {} exists and is non-empty.".format(dest))
    for d in DIRS:
        os.makedirs(os.path.join(dest, d), exist_ok=True)
        if d.startswith(("raw/", "wiki/", "builder/entries")):
            open(os.path.join(dest, d, ".gitkeep"), "a").close()
    for fn in ENGINE_FILES:
        src = os.path.join(BUILDER_DIR, fn)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dest, "builder", fn))
    templates_src = os.path.join(BUILDER_DIR, "templates")
    templates_dest = os.path.join(dest, "builder", "templates")
    _copy_tree(templates_src, templates_dest)
    with open(os.path.join(dest, "builder", "data.py"), "w") as f:
        f.write(STARTER_DATA.format(name=name))
    open(os.path.join(dest, "index.md"), "w").write("# Index\n\n*(empty — run builder/build.py)*\n")
    open(os.path.join(dest, "log.md"), "w").write(
        "# Log\n\n## [setup] {} scaffolded with builder/new_vault.py.\n".format(name))
    open(os.path.join(dest, "wiki", "overview.md"), "w").write(
        "# {} — Overview\n\n*(hand-maintained)*\n".format(name))
    open(os.path.join(dest, ".gitignore"), "w").write(
        "builder/cache/\nbuilder/__pycache__/\n.DS_Store\n")
    sys.path.insert(0, os.path.join(dest, "builder"))
    try:
        from docks_util import seed_docks
        seed_docks(dest)
    except Exception as ex:
        print("warning: could not seed docks.yaml:", ex)
    print("Scaffolded '{}' at {}".format(name, dest))
    print("Next: dock files to raw/, run map_channel + build, edit builder/entries/")


if __name__ == "__main__":
    main()
