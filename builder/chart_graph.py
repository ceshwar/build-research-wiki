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
from slug_util import canonical_slug, build_theme_resolver, merge_theme_slugs

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
            targets.append(canonical_slug(name) or name)
    return targets


def _slug_resolver(registry, paper_slugs, theme_titles):
    """Map any slug variant to one canonical node id."""
    theme_meta = {slug: (title, "", True) for slug, title in theme_titles.items()}
    all_slugs = set(registry.keys()) | set(paper_slugs) | set(theme_titles.keys())
    for reg_slug in registry:
        canon = canonical_slug(reg_slug)
        if canon:
            all_slugs.add(canon)
    aliases, _canonical = merge_theme_slugs(all_slugs, theme_meta)
    for reg_slug in registry:
        canon = canonical_slug(reg_slug)
        preferred = aliases.get(reg_slug) or aliases.get(canon) or canon or reg_slug
        aliases[reg_slug] = preferred
        if canon:
            aliases[canon] = preferred
    return aliases


def _resolve(registry, resolver, slug, resolve_theme=None):
    if not slug:
        return slug
    if resolve_theme:
        slug = resolve_theme(slug)
    canon = canonical_slug(slug)
    if slug in registry:
        return resolver.get(slug, resolver.get(canon, canon or slug))
    return resolver.get(slug, resolver.get(canon, canon or slug))


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
        canon = canonical_slug(slug) or slug
        entry = {
            "slug": canon,
            "type": node_type,
            "wiki_page": rel,
            "title": title,
        }
        # Prefer the lowercase kebab filename when two paths collide.
        if canon not in registry or slug == canon:
            registry[canon] = entry
        registry[slug] = entry
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
    data_path = os.path.join(vault, "builder", "data.py")
    themes_dict = {}
    if os.path.isfile(data_path):
        themes_dict = getattr(completion._load_module(data_path), "THEMES", {})
    resolve_theme, merged_themes, theme_aliases = build_theme_resolver(themes_dict)
    theme_titles = {slug: meta[0] for slug, meta in merged_themes.items()}

    paper_meta = {
        e["slug"]: {
            "title": e["title"],
            "status": e["status"],
            "wiki_page": e["wiki_page"],
            "themes": [resolve_theme(t) for t in (e.get("themes") or [])],
            "human_verified": e.get("human_verified"),
            "needs_human_verification": e.get("needs_human_verification"),
            "territory": e.get("territory"),
        }
        for e in entries
    }
    paper_slugs = set(paper_meta.keys())
    resolver = _slug_resolver(registry, paper_slugs, theme_titles)
    for variant, preferred in theme_aliases.items():
        resolver[variant] = preferred
        resolver[canonical_slug(variant)] = preferred

    visited = set(paper_slugs)
    edges = []
    edge_keys = set()

    def add_edge(source, target, kind="link"):
        source = _resolve(registry, resolver, source, resolve_theme)
        target = _resolve(registry, resolver, target, resolve_theme)
        if source == target:
            return
        visited.add(source)
        visited.add(target)
        key = (source, target, kind)
        if key in edge_keys:
            return
        edge_keys.add(key)
        edges.append({"source": source, "target": target, "kind": kind})

    # Structural paper → theme edges from chart data
    for slug, meta in paper_meta.items():
        for theme in meta["themes"]:
            add_edge(slug, theme, "theme")

    # Wikilink closure from charted papers through the wiki
    frontier = list(paper_slugs)
    scanned = set()
    while frontier:
        slug = frontier.pop()
        slug = _resolve(registry, resolver, slug, resolve_theme)
        if slug in scanned:
            continue
        scanned.add(slug)

        wiki_page = None
        if slug in paper_meta:
            wiki_page = paper_meta[slug]["wiki_page"]
        elif slug in registry:
            wiki_page = registry[slug]["wiki_page"]
        else:
            for reg_slug, reg in registry.items():
                if _resolve(registry, resolver, reg_slug) == slug:
                    wiki_page = reg["wiki_page"]
                    break
        if not wiki_page:
            continue

        abs_path = os.path.join(vault, wiki_page)
        if not os.path.isfile(abs_path):
            continue
        text = completion._read_text(abs_path)
        for target in _parse_wikilinks(text):
            resolved = _resolve(registry, resolver, target, resolve_theme)
            if resolved not in registry and resolved not in paper_slugs:
                continue
            if resolved not in scanned:
                frontier.append(resolved)
            add_edge(slug, resolved, "link")

    nodes = []
    stats = {}
    for slug in sorted(visited):
        slug = _resolve(registry, resolver, slug, resolve_theme)
        if any(n["id"] == slug for n in nodes):
            continue
        if slug in paper_meta:
            pm = paper_meta[slug]
            node_type = "paper"
            title = pm["title"]
            wiki_page = pm["wiki_page"]
            status = pm["status"]
            human_verified = pm.get("human_verified")
            needs_human_verification = pm.get("needs_human_verification")
            territory = pm.get("territory")
        elif slug in registry:
            reg = registry[slug]
            node_type = reg["type"]
            title = reg["title"]
            wiki_page = reg["wiki_page"]
            status = None
            human_verified = None
            needs_human_verification = None
            territory = None
            if node_type == "theme" and slug in theme_titles:
                title = theme_titles[slug]
        else:
            node_type = "theme"
            title = theme_titles.get(slug, slug.replace("-", " "))
            wiki_page = "wiki/themes/{}.md".format(slug)
            status = None
            human_verified = None
            needs_human_verification = None
            territory = None

        stats[node_type] = stats.get(node_type, 0) + 1
        node = {
            "id": slug,
            "slug": slug,
            "label": title,
            "type": node_type,
            "wiki_page": wiki_page,
            "status": status,
        }
        if node_type == "paper":
            node["human_verified"] = human_verified
            node["needs_human_verification"] = needs_human_verification
            node["territory"] = territory
        nodes.append(node)

    return {
        "channel_id": channel_id,
        "nodes": nodes,
        "edges": edges,
        "stats": stats,
        "message": "",
    }
