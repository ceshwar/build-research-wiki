#!/usr/bin/env python3
"""ENGINE (generic, do not edit per-vault): builds wiki/concepts and wiki/entities from
data.CONCEPTS / PEOPLE / PLATFORMS / METHODS, with backlinks to the papers using each.
Call build(root, data, today)."""
import os


def build(root, data, today):
    TITLES = data.TITLES
    CD = os.path.join(root, "wiki/concepts")
    ED = os.path.join(root, "wiki/entities")
    os.makedirs(CD, exist_ok=True)
    os.makedirs(ED, exist_ok=True)

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
        write(CD, slug, "concept", name, "", defn, papers, "[[overview|Portfolio overview]] · [[index]]")
    for slug, (name, role, defn, papers) in data.PEOPLE.items():
        write(ED, slug, "entity", name, role, defn, papers, "[[overview|Portfolio overview]]")
    for slug, (name, kind, defn, papers) in {**data.PLATFORMS, **data.METHODS}.items():
        write(ED, slug, "entity", name, kind, defn, papers, "[[overview|Portfolio overview]]")

    return {"concepts": len(data.CONCEPTS),
            "entities": len(data.PEOPLE) + len(data.PLATFORMS) + len(data.METHODS)}
