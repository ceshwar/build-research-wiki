#!/usr/bin/env python3
"""Single entrypoint to (re)generate the wiki for the vault this builder lives in.

    python3 builder/build.py            # build the parent vault
    python3 builder/build.py --vault /path/to/OtherVault

Portable: the vault is auto-detected as the parent of this builder/ folder, so copying the
whole vault elsewhere (or cloning it for a new corpus) just works. Idempotent.

Generated:  wiki/papers, wiki/themes, wiki/sources (docked), wiki/concepts, wiki/entities, index.md
Hand-kept:  wiki/overview.md, wiki/syntheses/, log.md, CLAUDE.md, BUILD.md
Chart entries: builder/entries/<channel>/<slug>.md  (deterministic — edit here, not raw/)
Deep dives: builder/deepdives/<slug>.md  (generative — LLM Deep Dive later)
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

    auto_path = os.path.join(builder, "auto_papers.py")
    if os.path.exists(auto_path):
        spec_auto = importlib.util.spec_from_file_location("auto_papers", auto_path)
        auto_mod = importlib.util.module_from_spec(spec_auto)
        spec_auto.loader.exec_module(auto_mod)
        mod.P = list(mod.P) + list(getattr(auto_mod, "P_AUTO", []))

    auto_lab = os.path.join(builder, "auto_lab_papers.py")
    if os.path.exists(auto_lab):
        spec_lab = importlib.util.spec_from_file_location("auto_lab_papers", auto_lab)
        lab_mod = importlib.util.module_from_spec(spec_lab)
        spec_lab.loader.exec_module(lab_mod)
        mod.P = list(mod.P) + list(getattr(lab_mod, "P_LAB_AUTO", []))

    auto_sources = os.path.join(builder, "auto_sources.py")
    if os.path.exists(auto_sources):
        spec_src = importlib.util.spec_from_file_location("auto_sources", auto_sources)
        src_mod = importlib.util.module_from_spec(spec_src)
        spec_src.loader.exec_module(src_mod)
        mod.S = list(getattr(mod, "S", [])) + list(getattr(src_mod, "S_AUTO", []))
    elif not hasattr(mod, "S"):
        mod.S = []

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
    data_path = os.path.join(builder, "data.py")
    if not os.path.exists(data_path):
        data_path = os.path.join(vault, "builder", "data.py")

    import incremental
    force_full = "--full" in sys.argv
    force_incr = "--incremental" in sys.argv

    if force_full:
        mode = "full"
        rebuild_papers = rebuild_themes = None
    elif force_incr or (not force_full and incremental.wiki_exists(vault)):
        mode = "incremental"
        rebuild_papers, rebuild_themes = incremental.plan(vault, data_path, deepdives, data)
        if not rebuild_papers and not rebuild_themes:
            mode = "up-to-date"
    else:
        mode = "full"
        rebuild_papers = rebuild_themes = None

    data_mtime = os.path.getmtime(data_path) if os.path.exists(data_path) else 0.0

    import engine_papers, engine_web, engine_ingest

    if mode == "up-to-date":
        s1 = {"papers": len(data.P), "themes": len(data.THEMES),
              "papers_built": 0, "themes_built": 0,
              "papers_skipped": len(data.P), "themes_skipped": len(data.THEMES),
              "no-pdf": [], "inferred": []}
        s2 = {"concepts": len(data.CONCEPTS),
              "entities": len(data.PEOPLE) + len(data.PLATFORMS) + len(data.METHODS),
              "concepts_built": 0, "entities_built": 0,
              "concepts_skipped": len(data.CONCEPTS),
              "entities_skipped": len(data.PEOPLE) + len(data.PLATFORMS) + len(data.METHODS)}
        s3 = engine_ingest.build(vault, data, today)
        if s3["sources_built"] > 0:
            mode = "incremental"
    else:
        s1 = engine_papers.build(vault, deepdives, data, today,
                                 rebuild_papers=rebuild_papers,
                                 rebuild_themes=rebuild_themes)
        s2 = engine_web.build(vault, data, today,
                              rebuild_papers=rebuild_papers,
                              data_mtime=data_mtime)
        s3 = engine_ingest.build(vault, data, today)

    red = link_check(vault)
    unmapped = incremental.unmapped_pdfs(vault, data)

    name = getattr(data, "VAULT", {}).get("name", os.path.basename(vault))
    print(f"[{name}]  {vault}")
    print(f"  mode: {mode}")
    if mode == "incremental":
        print(f"  updated: {s1['papers_built']} papers · {s1['themes_built']} themes · "
              f"{s2['concepts_built']} concepts · {s2['entities_built']} entities")
        print(f"  skipped: {s1['papers_skipped']} papers · {s1['themes_skipped']} themes · "
              f"{s2['concepts_skipped']} concepts · {s2['entities_skipped']} entities")
    elif mode == "up-to-date":
        print(f"  nothing to update (all pages current)")
    else:
        print(f"  papers {s1['papers']} · themes {s1['themes']} · concepts {s2['concepts']} · entities {s2['entities']}")
    if getattr(data, "S", []):
        print(f"  docked sources {s3['sources']} (built {s3['sources_built']})")
    if unmapped:
        print(f"  unmapped PDFs ({len(unmapped)}): {', '.join(unmapped)}")
        print(f"  → run: python3 builder/map_channel.py --vault {vault}")
    if s1.get("no-pdf"):
        print(f"  no-pdf ({len(s1['no-pdf'])}): {', '.join(s1['no-pdf'])}")
    if s1.get("inferred"):
        print(f"  inferred: {', '.join(s1['inferred'])}")
    print(f"  red links: {'NONE' if not red else red}")
    return 1 if red else 0


if __name__ == "__main__":
    sys.path.insert(0, BUILDER_DIR)
    sys.exit(main())
