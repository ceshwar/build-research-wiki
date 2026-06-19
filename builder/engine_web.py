#!/usr/bin/env python3
"""ENGINE (generic, do not edit per-vault): builds wiki/concepts and wiki/entities from
data.CONCEPTS / PEOPLE / PLATFORMS / METHODS, with backlinks to the papers using each.
Call build(root, data, today)."""
import os


def build(root, data, today, rebuild_papers=None, data_mtime=0.0):
    """Build concept/entity pages. Skip unchanged entries when rebuild_papers is a set."""
    TITLES = data.TITLES
    CD = os.path.join(root, "wiki/concepts")
    ED = os.path.join(root, "wiki/entities")
    os.makedirs(CD, exist_ok=True)
    os.makedirs(ED, exist_ok=True)

    concepts_built = entities_built = 0
    concepts_skipped = entities_skipped = 0

    def should_rebuild(papers, out_path):
        if rebuild_papers is None:
            return True
        if not os.path.exists(out_path):
            return True
        if data_mtime > _mtime(out_path):
            return True
        return bool(set(papers) & rebuild_papers)

    def _mtime(path):
        return os.path.getmtime(path) if os.path.exists(path) else 0.0

    def plink(s):
        return f"[[{s}|{TITLES.get(s, s)}]]"

    def write(d, slug, typ, name, sub, defn, papers, extra_links=""):
        ps = sorted(set(papers))
        lines = ["---", f"type: {typ}", f'title: "{name}"', f"slug: {slug}",
                 f"paper_count: {len(ps)}", f"updated: {today}", "---", "",
                 f"# {name}", "", f"> {defn}", ""]
        if sub:
            lines += [f"*{sub}*", ""]
        lines += ["## Appears in", ""]
        for p in ps:
            lines.append(f"- {plink(p)}")
        if extra_links:
            lines += ["", "## See also", "", extra_links]
        with open(os.path.join(d, slug + ".md"), "w") as f:
            f.write("\n".join(x for x in lines if x is not None) + "\n")

    for slug, (name, defn, papers) in data.CONCEPTS.items():
        out = os.path.join(CD, slug + ".md")
        if not should_rebuild(papers, out):
            concepts_skipped += 1
            continue
        concepts_built += 1
        write(CD, slug, "concept", name, "", defn, papers, "[[overview|Portfolio overview]] · [[index]]")
    for slug, (name, role, defn, papers) in data.PEOPLE.items():
        out = os.path.join(ED, slug + ".md")
        if not should_rebuild(papers, out):
            entities_skipped += 1
            continue
        entities_built += 1
        write(ED, slug, "entity", name, role, defn, papers, "[[overview|Portfolio overview]]")
    for slug, (name, kind, defn, papers) in {**data.PLATFORMS, **data.METHODS}.items():
        out = os.path.join(ED, slug + ".md")
        if not should_rebuild(papers, out):
            entities_skipped += 1
            continue
        entities_built += 1
        write(ED, slug, "entity", name, kind, defn, papers, "[[overview|Portfolio overview]]")

    return {"concepts": len(data.CONCEPTS),
            "entities": len(data.PEOPLE) + len(data.PLATFORMS) + len(data.METHODS),
            "concepts_built": concepts_built, "entities_built": entities_built,
            "concepts_skipped": concepts_skipped, "entities_skipped": entities_skipped}
