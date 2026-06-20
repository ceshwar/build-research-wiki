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


def _strip_frontmatter(text):
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3 :]
    return text


def _wiki_blockquote_overview(text):
    """First blockquote after the H1 — the paper one-liner on chart pages."""
    text = _strip_frontmatter(text).lstrip()
    h1 = re.search(r"^#\s+.+$", text, re.M)
    if not h1:
        return ""
    rest = text[h1.end() :].lstrip("\n")
    quote_lines = []
    for ln in rest.splitlines():
        s = ln.strip()
        if s.startswith(">"):
            quote_lines.append(re.sub(r"^>\s*", "", s))
        elif quote_lines:
            break
        elif s.startswith("**") or s.startswith("[!"):
            break
    overview = " ".join(quote_lines).strip()
    if not overview or overview in ("—", "-") or completion._is_placeholder(overview):
        return ""
    return overview


def _abstract_snippet(text, limit=240):
    for heading in ("Abstract / Notes", "Abstract", "Summary"):
        block = completion._section_text(text, heading)
        if not block or len(block.strip()) < 40 or completion._is_placeholder(block):
            continue
        para = block.strip().split("\n\n")[0].replace("\n", " ")
        if len(para) > limit:
            para = para[:limit].rsplit(" ", 1)[0] + "…"
        return para
    return ""


def _overview_for(item, vault, wiki_page, channel_id):
    """One-line overview: wiki blockquote → entry one-liner → registry → abstract snippet."""
    wiki_abs = os.path.join(vault, wiki_page)
    wiki_text = completion._read_text(wiki_abs) if os.path.isfile(wiki_abs) else ""

    if wiki_text:
        overview = _wiki_blockquote_overview(wiki_text)
        if overview:
            return overview

    entry_rel = item.get("entry") or item.get("note", "")
    entry_abs = completion._resolve_entry_path(vault, entry_rel, item.get("channel", channel_id))
    if entry_abs:
        parsed = completion._parse_entry(entry_abs)
        one = (parsed.get("one_liner") or "").strip()
        if one and not completion._is_placeholder(one):
            return one

    registry_one = (item.get("one") or "").strip()
    if registry_one and not completion._is_placeholder(registry_one):
        return registry_one

    if wiki_text:
        snippet = _abstract_snippet(wiki_text)
        if snippet:
            return snippet
    return ""


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

    entries = []
    for item in sorted(corpus, key=lambda x: (-(x.get("year") or 0), x.get("title", x["slug"]))):
        assessed = completion.assess_entry(vault, item)
        paper_slug = item["slug"]
        wiki_page = (
            "wiki/papers/{}.md".format(paper_slug)
            if ch.get("profile") == "portfolio"
            else "wiki/sources/{}.md".format(paper_slug)
        )
        entries.append({
            "slug": paper_slug,
            "title": item.get("title") or paper_slug,
            "status": assessed["status"],
            "year": item.get("year") or None,
            "venue": item.get("venue") or "",
            "pdf": _pdf_name(item, channels),
            "pdf_path": _pdf_path(item, channel_id, channels),
            "themes": _themes_for(item, vault),
            "overview": _overview_for(item, vault, wiki_page, channel_id),
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
