#!/usr/bin/env python3
"""Single entrypoint to (re)generate the wiki for the vault this builder lives in.

    python3 builder/build.py            # build the parent vault
    python3 builder/build.py --vault /path/to/OtherVault

Portable: the vault is auto-detected as the parent of this builder/ folder, so copying the
whole vault elsewhere (or cloning it for a new corpus) just works. Idempotent.

Generated:  wiki/papers, wiki/themes, wiki/concepts, wiki/entities, index.md
Hand-kept:  wiki/overview.md, wiki/syntheses/, log.md, CLAUDE.md, BUILD.md
Deep dives: builder/deepdives/<slug>.md  (source of truth, injected into paper pages)
"""
import os, sys, re, glob, datetime, importlib.util

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))


def load_data(vault_root):
    """Load the data.py that belongs to the target vault's builder (defaults to this one)."""
    builder = os.path.join(vault_root, "builder")
    data_path = os.path.join(builder, "data.py")
    if not os.path.exists(data_path):          # building this vault in place
        builder, data_path = BUILDER_DIR, os.path.join(BUILDER_DIR, "data.py")
    spec = importlib.util.spec_from_file_location("data", data_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, builder


def link_check(root):
    files = {os.path.splitext(os.path.basename(p))[0]
             for p in glob.glob(os.path.join(root, "wiki/**/*.md"), recursive=True)
             + glob.glob(os.path.join(root, "*.md"))}
    red = set()
    for src in glob.glob(os.path.join(root, "wiki/**/*.md"), recursive=True):
        for raw in re.findall(r"\[\[([^\]]+)\]\]", open(src).read()):
            name = raw.split("|")[0].split("\\")[0].strip()
            if name and name not in files:
                red.add(name)
    return sorted(red)


def main():
    vault = os.path.dirname(BUILDER_DIR)
    if "--vault" in sys.argv:
        vault = os.path.abspath(sys.argv[sys.argv.index("--vault") + 1])
    today = datetime.date.today().isoformat()

    data, builder = load_data(vault)
    deepdives = os.path.join(builder, "deepdives")

    import engine_papers, engine_web
    s1 = engine_papers.build(vault, deepdives, data, today)
    s2 = engine_web.build(vault, data, today)
    red = link_check(vault)

    name = getattr(data, "VAULT", {}).get("name", os.path.basename(vault))
    print(f"[{name}]  {vault}")
    print(f"  papers {s1['papers']} · themes {s1['themes']} · concepts {s2['concepts']} · entities {s2['entities']}")
    if s1["no-pdf"]:
        print(f"  no-pdf ({len(s1['no-pdf'])}): {', '.join(s1['no-pdf'])}")
    if s1["inferred"]:
        print(f"  inferred: {', '.join(s1['inferred'])}")
    print(f"  red links: {'NONE' if not red else red}")
    return 1 if red else 0


if __name__ == "__main__":
    sys.path.insert(0, BUILDER_DIR)
    sys.exit(main())
