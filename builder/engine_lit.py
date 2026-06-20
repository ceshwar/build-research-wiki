#!/usr/bin/env python3
"""Generate the external-literature layer (wiki/lit/) from builder/lit/store.json.

The field layer is a parallel, clearly-separated corpus (type: extpaper, corpus: field)
seeded from what the portfolio cites. This engine is deterministic: it renders pages from
the store and never invents an edge. Enrichment (themes/concepts/one-liner/relates and the
deep dive) is added by the manual agent and read back from the store + builder/deepdives/.

Plugs into build.py after the portfolio engines; the shared red-link check covers wiki/lit/.
See docs/LIT-EXPANSION-SPEC.md §1.
"""
import datetime
import json
import os

VALID_DEPTHS = ("stub", "mapped", "deepdive")


def _load_store(builder_dir):
    path = os.path.join(builder_dir, "lit", "store.json")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("works", [])


def _resolve_cited_by(records):
    """Forward edges within the KB: who cites whom (derived, never invented)."""
    by_slug = {r["slug"]: r for r in records}
    derived = {r["slug"]: set(r.get("cited_by", []) or []) for r in records}
    for r in records:
        for tgt in r.get("cites", []) or []:
            if tgt in by_slug:
                derived[tgt].add(r["slug"])
    for r in records:
        r["cited_by"] = sorted(derived[r["slug"]])


def _yaml_list(items):
    return "[" + ", ".join(items) + "]"


def _frontmatter(r):
    title = (r.get("title") or r["slug"]).replace('"', "'")
    ids = r.get("ids", {}) or {}
    fm = ["---", "type: extpaper", "corpus: field", 'title: "{}"'.format(title)]
    if r.get("authors"):
        fm.append("authors: {}".format(_yaml_list(r["authors"])))
    fm.append("venue: {}".format(r.get("venue", "") or ""))
    fm.append("year: {}".format(r.get("year", "") if r.get("year") is not None else ""))
    if ids:
        fm.append("ids:")
        for k in ("openalex", "doi", "arxiv"):
            if ids.get(k):
                fm.append("  {}: {}".format(k, ids[k]))
    if r.get("url"):
        fm.append("url: {}".format(r["url"]))
    depth = r.get("depth", "stub")
    fm.append("depth: {}".format(depth if depth in VALID_DEPTHS else "stub"))
    fm.append("seed_from: {}".format(_yaml_list(r.get("seed_from", []) or [])))
    fm.append("discovered_via: {}".format(r.get("discovered_via", "portfolio-citation")))
    if depth in ("mapped", "deepdive"):
        fm.append("themes: {}".format(_yaml_list(r.get("themes", []) or [])))
        fm.append("concepts: {}".format(_yaml_list(r.get("concepts", []) or [])))
    fm.append("cites: {}".format(_yaml_list(r.get("cites", []) or [])))
    fm.append("cited_by: {}".format(_yaml_list(r.get("cited_by", []) or [])))
    fm.append("added: {}".format(r.get("added", "")))
    if r.get("note"):
        fm.append('note: "{}"'.format(r["note"].replace('"', "'")))
    fm.append("---")
    return fm


def _render_page(root, r):
    depth = r.get("depth", "stub")
    L = _frontmatter(r)
    L += ["", "# {}".format(r.get("title") or r["slug"]), ""]
    meta = " · ".join(x for x in [r.get("venue") or "", str(r.get("year") or "")] if x)
    L.append("> {} · _field literature_  **[external]**".format(meta or "external work"))
    L.append("")

    ids = r.get("ids", {}) or {}
    id_bits = []
    if ids.get("openalex"):
        id_bits.append("OpenAlex `{}`".format(ids["openalex"]))
    if ids.get("doi"):
        id_bits.append("DOI `{}`".format(ids["doi"]))
    if ids.get("arxiv"):
        id_bits.append("arXiv `{}`".format(ids["arxiv"]))
    if id_bits:
        L += ["**IDs:** " + " · ".join(id_bits), ""]
    if r.get("url"):
        L += ["**Link:** {}".format(r["url"]), ""]

    seeds = r.get("seed_from", []) or []
    if seeds:
        L += ["## Cited by your work", ""]
        L += ["- [[{}]]".format(s) for s in seeds]
        L.append("")

    if r.get("abstract"):
        L += ["## Abstract", "", r["abstract"].strip() + "  **[external]**", ""]

    if depth in ("mapped", "deepdive"):
        if r.get("one_liner"):
            L += ["## One-liner", "", r["one_liner"].strip(), ""]
        tags = []
        if r.get("themes"):
            tags.append("**Themes:** " + ", ".join("[[{}]]".format(t) for t in r["themes"]))
        if r.get("concepts"):
            tags.append("**Concepts:** " + ", ".join("[[{}]]".format(c) for c in r["concepts"]))
        if tags:
            L += tags + [""]
        if r.get("relates"):
            L += ["## How it relates to the portfolio", "", r["relates"].strip(), ""]

    if depth == "deepdive":
        dd_path = os.path.join(root, "builder", "deepdives", r["slug"] + ".md")
        if os.path.exists(dd_path):
            with open(dd_path) as f:
                dd = f.read().strip()
            L += ["## Deep dive", "", dd, ""]
        else:
            L += ["## Deep dive", "", "*Deep dive pending — fill `builder/deepdives/{}.md`.*".format(r["slug"]), ""]

    cited_by = r.get("cited_by", []) or []
    if cited_by:
        L += ["## Cited by (in this wiki)", ""]
        L += ["- [[{}]]".format(c) for c in cited_by]
        L.append("")

    if r.get("note"):
        L += ["> [!note] {}".format(r["note"]), ""]
    return "\n".join(L).rstrip() + "\n"


def _render_index(records, today):
    L = ["---", "type: index", "corpus: field", "updated: {}".format(today), "---", "",
         "# Field Literature", "",
         "> External work cited by the portfolio (`corpus: field`) — a parallel layer, "
         "separate from the portfolio map.", ""]
    counts = {d: sum(1 for r in records if r.get("depth", "stub") == d) for d in VALID_DEPTHS}
    L.append("**{}** external works · {} stub · {} mapped · {} deepdive".format(
        len(records), counts["stub"], counts["mapped"], counts["deepdive"]))
    L.append("")
    ordered = sorted(records,
                     key=lambda r: (-len(r.get("seed_from", []) or []), -(r.get("cited_by_count") or 0)))
    L += ["## Works", ""]
    for r in ordered:
        title = r.get("title") or r["slug"]
        meta = " ".join(x for x in [r.get("venue") or "", str(r.get("year") or "")] if x)
        seeds = ", ".join("[[{}]]".format(s) for s in (r.get("seed_from", []) or []))
        L.append("- [[{}|{}]] — {} · seeds: {} · _{}_".format(
            r["slug"], title, meta or "—", seeds or "—", r.get("depth", "stub")))
    L.append("")
    L += ["## See also", "", "[[overview]] · [[index|portfolio index]] · [[CLAUDE|schema]]", ""]
    return "\n".join(L)


def _write_if_changed(path, content):
    """Idempotent write — leaves mtime alone when nothing changed (safe on every build)."""
    if os.path.exists(path):
        with open(path) as f:
            if f.read() == content:
                return False
    with open(path, "w") as f:
        f.write(content)
    return True


def build(root, today=None, rebuild_slugs=None):
    today = today or datetime.date.today().isoformat()
    builder_dir = os.path.join(root, "builder")
    records = _load_store(builder_dir)
    if not records:
        return {"lit": 0, "lit_built": 0}

    _resolve_cited_by(records)
    lit_dir = os.path.join(root, "wiki", "lit")
    os.makedirs(lit_dir, exist_ok=True)

    built = 0
    for r in records:
        if rebuild_slugs is not None and r["slug"] not in rebuild_slugs:
            continue
        if _write_if_changed(os.path.join(lit_dir, r["slug"] + ".md"), _render_page(root, r)):
            built += 1

    _write_if_changed(os.path.join(lit_dir, "index.md"), _render_index(records, today))
    return {"lit": len(records), "lit_built": built}
