#!/usr/bin/env python3
"""Wikilink graph for SCUBA UI — papers on chart + linked wiki nodes for a portfolio dock."""

import glob
import os
import re
import sys

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))
if BUILDER_DIR not in sys.path:
    sys.path.insert(0, BUILDER_DIR)

import chart_map
import completion

WIKI_FOLDER_TYPES = {
    "papers": "paper",
    "themes": "theme",
    "concepts": "concept",
    "entities": "entity",
    "syntheses": "synthesis",
    "sources": "source",
}


def _strip_frontmatter(text):
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3 :]
    return text


def _title_from_wiki(path):
    text = completion._read_text(path)
    if not text:
        return ""
    fm = {}
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            block = text[3:end]
            for line in block.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip().strip('"').strip("'")
    if fm.get("title"):
        return fm["title"]
    body = _strip_frontmatter(text).lstrip()
    m = re.search(r"^#\s+(.+)$", body, re.M)
    return m.group(1).strip() if m else ""


def _parse_wikilinks(text):
    targets = []
    for raw in re.findall(r"\[\[([^\]]+)\]\]", text):
        name = raw.split("|")[0].split("#")[0].strip()
        if name:
            targets.append(name)
    return targets


def _wiki_registry(vault):
    """slug -> {slug, type, wiki_page, title}"""
    registry = {}
    wiki_root = os.path.join(vault, "wiki")
    if not os.path.isdir(wiki_root):
        return registry
    for path in glob.glob(os.path.join(wiki_root, "**", "*.md"), recursive=True):
        rel = os.path.relpath(path, vault).replace("\\", "/")
        parts = rel.split("/")
        if len(parts) < 3 or parts[0] != "wiki":
            continue
        folder = parts[1]
        slug = os.path.splitext(parts[2])[0]
        node_type = WIKI_FOLDER_TYPES.get(folder, "page")
        title = _title_from_wiki(path) or slug.replace("-", " ")
        registry[slug] = {
            "slug": slug,
            "type": node_type,
            "wiki_page": rel,
            "title": title,
        }
    return registry


def _empty_graph(channel_id, reason=""):
    return {
        "channel_id": channel_id,
        "nodes": [],
        "edges": [],
        "stats": {},
        "message": reason,
    }


def build_graph(vault, channel_id="my-portfolio"):
    """Graph nodes/edges for charted papers and wiki links (portfolio docks only)."""
    vault = os.path.abspath(vault)
    chart = chart_map.build_map(vault, channel_id)
    if chart.get("profile") != "portfolio":
        return _empty_graph(channel_id, "Graph view is available for portfolio docks only.")

    entries = chart.get("entries") or []
    if not entries:
        return _empty_graph(channel_id)

    registry = _wiki_registry(vault)
    theme_titles = {t["slug"]: t["title"] for t in chart.get("themes") or []}

    paper_meta = {
        e["slug"]: {
            "title": e["title"],
            "status": e["status"],
            "wiki_page": e["wiki_page"],
            "themes": e.get("themes") or [],
        }
        for e in entries
    }
    paper_slugs = set(paper_meta.keys())

    visited = set(paper_slugs)
    edges = []
    edge_keys = set()

    def add_edge(source, target, kind="link"):
        if source == target:
            return
        key = (source, target, kind)
        if key in edge_keys:
            return
        edge_keys.add(key)
        edges.append({"source": source, "target": target, "kind": kind})

    # Structural paper → theme edges from chart data
    for slug, meta in paper_meta.items():
        for theme in meta["themes"]:
            visited.add(theme)
            add_edge(slug, theme, "theme")

    # Wikilink closure from charted papers through the wiki
    frontier = list(paper_slugs)
    scanned = set()
    while frontier:
        slug = frontier.pop()
        if slug in scanned:
            continue
        scanned.add(slug)

        wiki_page = None
        if slug in paper_meta:
            wiki_page = paper_meta[slug]["wiki_page"]
        elif slug in registry:
            wiki_page = registry[slug]["wiki_page"]
        if not wiki_page:
            continue

        abs_path = os.path.join(vault, wiki_page)
        if not os.path.isfile(abs_path):
            continue
        text = completion._read_text(abs_path)
        for target in _parse_wikilinks(text):
            if target not in registry and target not in paper_slugs:
                continue
            if target not in visited:
                visited.add(target)
                frontier.append(target)
            add_edge(slug, target, "link")

    nodes = []
    stats = {}
    for slug in sorted(visited):
        if slug in paper_meta:
            pm = paper_meta[slug]
            node_type = "paper"
            title = pm["title"]
            wiki_page = pm["wiki_page"]
            status = pm["status"]
        elif slug in registry:
            reg = registry[slug]
            node_type = reg["type"]
            title = reg["title"]
            wiki_page = reg["wiki_page"]
            status = None
            if node_type == "theme" and slug in theme_titles:
                title = theme_titles[slug]
        else:
            node_type = "theme"
            title = theme_titles.get(slug, slug.replace("-", " "))
            wiki_page = "wiki/themes/{}.md".format(slug)
            status = None

        stats[node_type] = stats.get(node_type, 0) + 1
        nodes.append({
            "id": slug,
            "slug": slug,
            "label": title,
            "type": node_type,
            "wiki_page": wiki_page,
            "status": status,
        })

    return {
        "channel_id": channel_id,
        "nodes": nodes,
        "edges": edges,
        "stats": stats,
        "message": "",
    }
