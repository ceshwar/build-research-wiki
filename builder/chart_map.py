#!/usr/bin/env python3
"""Chart map for SCUBA UI — papers on chart + raw dock files for a channel."""

import os
import re
import sys

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))
if BUILDER_DIR not in sys.path:
    sys.path.insert(0, BUILDER_DIR)

import completion
import ingest_prompt
from docks_util import load_channel_map, resolve_raw_dirs, get_dock


def _load_themes(vault):
    data_path = os.path.join(vault, "builder", "data.py")
    if not os.path.exists(data_path):
        return []
    data = completion._load_module(data_path)
    themes = getattr(data, "THEMES", {})
    return [{"slug": slug, "title": meta[0]} for slug, meta in sorted(themes.items())]


def _concepts_by_paper(vault):
    """Invert builder/data.py CONCEPTS → paper slug → [{slug, title}, …]."""
    data_path = os.path.join(vault, "builder", "data.py")
    if not os.path.exists(data_path):
        return {}
    data = completion._load_module(data_path)
    concepts = getattr(data, "CONCEPTS", {})
    by_paper = {}
    for slug, meta in concepts.items():
        title = meta[0] if meta else slug
        papers = meta[2] if len(meta) > 2 else []
        for paper in papers:
            by_paper.setdefault(paper, []).append({"slug": slug, "title": title})
    for paper in by_paper:
        by_paper[paper].sort(key=lambda c: c["slug"])
    return by_paper


def _wiki_concept_slugs(vault):
    concepts_dir = os.path.join(vault, "wiki", "concepts")
    if not os.path.isdir(concepts_dir):
        return set()
    return {
        f[:-3] for f in os.listdir(concepts_dir)
        if f.endswith(".md") and not f.startswith(".")
    }


def _concepts_from_wiki_page(vault, wiki_page, known_slugs):
    path = os.path.join(vault, wiki_page)
    if not os.path.isfile(path) or not known_slugs:
        return []
    text = completion._read_text(path)
    found = []
    seen = set()
    for m in re.finditer(r"\[\[([^\]|#]+)(?:\|[^\]]+)?\]\]", text):
        slug = m.group(1).strip()
        if slug in known_slugs and slug not in seen:
            seen.add(slug)
            title = slug.replace("-", " ").title()
            concept_path = os.path.join(vault, "wiki", "concepts", slug + ".md")
            if os.path.isfile(concept_path):
                page = completion._read_text(concept_path)
                fm = re.search(r"^title:\s*[\"']?(.+?)[\"']?\s*$", page, re.M)
                if fm:
                    title = fm.group(1).strip()
            found.append({"slug": slug, "title": title})
    return sorted(found, key=lambda c: c["slug"])


def _syntheses_by_paper(vault):
    """Scan wiki/syntheses for pages that wikilink each paper slug."""
    synth_dir = os.path.join(vault, "wiki", "syntheses")
    if not os.path.isdir(synth_dir):
        return {}
    by_paper = {}
    link_re = re.compile(r"\[\[([^\]|#]+)(?:\|[^\]]+)?\]\]")
    for fname in sorted(os.listdir(synth_dir)):
        if not fname.endswith(".md") or fname.startswith("."):
            continue
        slug = fname[:-3]
        path = os.path.join(synth_dir, fname)
        text = completion._read_text(path)
        title = slug.replace("-", " ").title()
        fm = re.search(r"^title:\s*[\"']?(.+?)[\"']?\s*$", text, re.M)
        if fm:
            title = fm.group(1).strip()
        else:
            h1 = re.search(r"^#\s+(.+)$", text, re.M)
            if h1:
                title = h1.group(1).strip()
        for m in link_re.finditer(text):
            paper = m.group(1).strip()
            by_paper.setdefault(paper, []).append({"slug": slug, "title": title})
    return by_paper


def _pdf_path(item, channel_id, channels):
    pdfs = item.get("pdfs") or []
    if not pdfs:
        return ""
    src = pdfs[0]
    if "/" not in src:
        raw_path = channels.get(channel_id, {}).get("raw_path", "raw/papers")
        src = "{}/{}".format(raw_path, src)
    return src


def _pdf_name(item, channels):
    pdfs = item.get("pdfs") or []
    if not pdfs:
        return ""
    src = pdfs[0]
    return os.path.basename(src)


def _themes_for(item, vault):
    entry_rel = item.get("entry") or item.get("note", "")
    entry_abs = completion._resolve_entry_path(
        vault, entry_rel, item.get("channel", "my-portfolio"))
    parsed = completion._parse_entry(entry_abs) if entry_abs else {"themes": []}
    reg = [t for t in (item.get("themes") or []) if t]
    parsed_t = [t for t in (parsed.get("themes") or []) if t]
    return parsed_t or reg


def _raw_files(vault, channel_id):
    dock = get_dock(vault, channel_id, create_if_missing=False)
    if not dock:
        return []
    exts = {e.lower().lstrip(".") for e in dock.get("extensions", ["pdf"])}
    files = []
    for raw_rel in resolve_raw_dirs(vault, dock):
        raw_dir = os.path.join(vault, raw_rel)
        if not os.path.isdir(raw_dir):
            continue
        for f in sorted(os.listdir(raw_dir)):
            if f.startswith("."):
                continue
            ext = os.path.splitext(f)[1].lower().lstrip(".")
            if ext in exts and f not in files:
                files.append(f)
    return files


def _charted_pdfs(corpus, channels):
    known = set()
    for item in corpus:
        for pdf in item.get("pdfs") or []:
            known.add(pdf)
            known.add(os.path.basename(pdf))
    return known


def build_map(vault, channel_id="my-portfolio"):
    """Return chart entries, themes, and raw dock files for the UI."""
    vault = os.path.abspath(vault)
    channels = load_channel_map(vault)
    ch = channels.get(channel_id, {})
    raw_path = ch.get("raw_path", "raw/papers")
    wiki_folder = "wiki/papers" if ch.get("profile") == "portfolio" else "wiki/sources"
    corpus = [
        e for e in ingest_prompt._full_corpus(vault)
        if e.get("channel") == channel_id
    ]
    known = _charted_pdfs(corpus, channels)
    raw_files = _raw_files(vault, channel_id)
    concepts_by_paper = _concepts_by_paper(vault)
    syntheses_by_paper = _syntheses_by_paper(vault)
    wiki_concepts = _wiki_concept_slugs(vault)

    entries = []
    for item in sorted(corpus, key=lambda x: (-(x.get("year") or 0), x.get("title", x["slug"]))):
        assessed = completion.assess_entry(vault, item)
        paper_slug = item["slug"]
        wiki_page = (
            "wiki/papers/{}.md".format(paper_slug)
            if ch.get("profile") == "portfolio"
            else "wiki/sources/{}.md".format(paper_slug)
        )
        registry_concepts = concepts_by_paper.get(paper_slug, [])
        wiki_linked = _concepts_from_wiki_page(vault, wiki_page, wiki_concepts)
        merged_concepts = list(registry_concepts)
        seen_c = {c["slug"] for c in merged_concepts}
        for c in wiki_linked:
            if c["slug"] not in seen_c:
                merged_concepts.append(c)
                seen_c.add(c["slug"])
        merged_concepts.sort(key=lambda c: c["slug"])
        entries.append({
            "slug": paper_slug,
            "title": item.get("title") or paper_slug,
            "status": assessed["status"],
            "year": item.get("year") or None,
            "venue": item.get("venue") or "",
            "pdf": _pdf_name(item, channels),
            "pdf_path": _pdf_path(item, channel_id, channels),
            "themes": _themes_for(item, vault),
            "concepts": merged_concepts,
            "syntheses": syntheses_by_paper.get(paper_slug, []),
            "entry": item.get("entry") or item.get("note", ""),
            "wiki_page": wiki_page,
        })

    awaiting = [f for f in raw_files if f not in known]

    return {
        "channel_id": channel_id,
        "channel_name": ch.get("name", channel_id),
        "profile": ch.get("profile", "portfolio"),
        "raw_path": raw_path,
        "wiki_folder": wiki_folder,
        "themes": _load_themes(vault),
        "entries": entries,
        "raw_files": raw_files,
        "awaiting_chart": awaiting,
    }
