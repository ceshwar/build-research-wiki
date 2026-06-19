#!/usr/bin/env python3
"""Assess chart entry completeness — scaffolded vs charted vs processed."""

import importlib.util
import os
import re

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))

PLACEHOLDER_MARKERS = (
    "theme-slug-one", "theme-slug-two", "theme-slug", "concept-slug",
    "(fill in", "(What does", "(Data, design", "(Main results",
    "(Major claims", "(Authors'", "(Concept/theme",
    "Pending LLM", "paste from paper", "Your abstract",
    "Your skim", "What happened", "Connections, TODOs",
    "Docked PDF", "Auto-mapped", "fill themes",
)

DEFAULT_ONES = (
    "Auto-mapped from PDF",
    "Docked PDF — fill",
    "Docked artifact — fill",
    "confirm themes and abstract",
)

PORTFOLIO_DEEPDIVE_SECTIONS = (
    "Authors", "Research question", "Method", "Findings",
    "Claims & evidence", "Limitations", "Contributes to",
)

INGEST_DEEPDIVE_SECTIONS = (
    "Authors", "Research question", "Method", "Findings",
    "Claims & evidence", "Limitations", "Relevance to my review",
)


def _load_module(path):
    spec = importlib.util.spec_from_file_location("mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_corpus(vault_path):
    """Return all registry entries as dicts with channel + profile."""
    builder = os.path.join(vault_path, "builder")
    data_path = os.path.join(builder, "data.py")
    entries = []

    if os.path.exists(data_path):
        data = _load_module(data_path)
        for p in getattr(data, "P", []):
            channel = p.get("channel")
            if not channel:
                pdfs = p.get("pdfs", [])
                channel = "lab-portfolio" if any("lab/" in x for x in pdfs) else "my-portfolio"
            entries.append({
                "profile": "portfolio",
                "channel": channel,
                "slug": p["slug"],
                "entry": p.get("entry") or p.get("note", ""),
                "one": p.get("one", ""),
                "themes": list(p.get("themes", [])),
                "title": p.get("title", p["slug"]),
                "status": p.get("status", "mapped"),
            })
        for s in getattr(data, "S", []):
            entries.append({
                "profile": "ingest",
                "channel": s.get("channel", "lit-review"),
                "slug": s["slug"],
                "entry": s.get("entry", ""),
                "one": s.get("one", ""),
                "themes": [],
                "title": s.get("title", s["slug"]),
                "status": s.get("status", "quick-dip"),
            })

    for auto_name, key, default_channel in [
        ("auto_papers.py", "P_AUTO", "my-portfolio"),
        ("auto_lab_papers.py", "P_LAB_AUTO", "lab-portfolio"),
        ("auto_sources.py", "S_AUTO", None),
    ]:
        auto_path = os.path.join(builder, auto_name)
        if not os.path.exists(auto_path):
            continue
        mod = _load_module(auto_path)
        for item in getattr(mod, key, []):
            channel = item.get("channel") or default_channel
            profile = "portfolio" if key.startswith("P_") else "ingest"
            entries.append({
                "profile": profile,
                "channel": channel,
                "slug": item["slug"],
                "entry": item.get("entry") or item.get("note", ""),
                "one": item.get("one", ""),
                "themes": list(item.get("themes", [])),
                "title": item.get("title", item["slug"]),
                "status": item.get("status", "quick-dip"),
            })
    return entries


def _read_text(path):
    if not path or not os.path.exists(path):
        return ""
    with open(path) as f:
        return f.read()


def _parse_theme_links(text):
    themes = []
    for line in text.splitlines()[:8]:
        s = line.strip()
        if s.startswith("<!--") or not s:
            continue
        for m in re.finditer(r"\[\[([^\]|]+)", s):
            slug = m.group(1).strip().lower()
            if slug and slug not in ("theme-slug", "theme-slug-one", "theme-slug-two"):
                themes.append(slug)
        if not s.startswith("[["):
            break
    return themes


def _section_text(text, heading):
    pattern = r"(?im)^#{{0,6}}\s*{}\s*$".format(re.escape(heading))
    m = re.search(pattern, text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"(?m)^#{{1,6}}\s+", rest)
    block = rest[: nxt.start()] if nxt else rest
    return block.strip()


def _parse_entry(entry_path):
    text = _read_text(entry_path)
    themes = _parse_theme_links(text)
    abstract = _section_text(text, "Abstract")
    if not abstract:
        body_lines = []
        started = False
        for ln in text.splitlines():
            s = ln.strip()
            if s.startswith("<!--"):
                continue
            if re.match(r"^\s*(\[\[.*\]\][,\s]*)+$", s):
                continue
            if s.lower().startswith("## abstract"):
                started = True
                continue
            if started:
                if s.startswith("## "):
                    break
                body_lines.append(ln)
        abstract = "\n".join(body_lines).strip()
    summary = _section_text(text, "Summary") or abstract
    one_liner = _section_text(text, "One-liner")
    return {
        "themes": themes,
        "abstract": abstract,
        "summary": summary,
        "one_liner": one_liner,
    }


def _is_placeholder(text):
    if not text or len(text.strip()) < 20:
        return True
    low = text.lower()
    return any(m.lower() in low for m in PLACEHOLDER_MARKERS)


def _one_complete(registry_one, parsed_one):
    for candidate in (parsed_one, registry_one):
        if not candidate:
            continue
        if any(d in candidate for d in DEFAULT_ONES):
            continue
        if len(candidate.strip()) >= 25 and not _is_placeholder(candidate):
            return True
    return False


def _abstract_complete(parsed, profile):
    body = parsed["summary"] if profile == "ingest" else parsed["abstract"]
    return bool(body) and len(body.strip()) >= 80 and not _is_placeholder(body)


def _themes_complete(registry_themes, parsed_themes):
    real = [t for t in (registry_themes or parsed_themes) if t]
    return len(real) >= 1


def _deepdive_section_filled(text, section):
    pattern = r"\*\*{}\.\*\*".format(re.escape(section))
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        pattern2 = r"\*\*{}\*\*".format(re.escape(section))
        m = re.search(pattern2, text, re.IGNORECASE)
    if not m:
        return False
    after = text[m.end():].strip()
    nxt = re.search(r"\n\*\*", after)
    content = (after[: nxt.start()] if nxt else after).strip()
    content = content.lstrip(".*: ").strip()
    return len(content) >= 25 and not _is_placeholder(content)


def _deepdive_complete(dd_path, profile):
    text = _read_text(dd_path)
    if not text or "*Deep dive pending" in text:
        return False
    sections = INGEST_DEEPDIVE_SECTIONS if profile == "ingest" else PORTFOLIO_DEEPDIVE_SECTIONS
    filled = sum(1 for s in sections if _deepdive_section_filled(text, s))
    core = ("Research question", "Method", "Findings")
    core_ok = all(_deepdive_section_filled(text, s) for s in core)
    return core_ok and filled >= 4


def _resolve_entry_path(vault_path, entry_rel, channel):
    if not entry_rel:
        return None
    entry_rel = entry_rel.replace("\\", "/")
    if entry_rel.startswith(("builder/", "raw/")):
        return os.path.join(vault_path, entry_rel)
    if "/" in entry_rel:
        return os.path.join(vault_path, entry_rel)
    if entry_rel.endswith(".md"):
        legacy = os.path.join(vault_path, "raw/notes/abstracts", entry_rel)
        if os.path.exists(legacy):
            return legacy
    return os.path.join(vault_path, "builder/entries", channel, entry_rel)


def assess_entry(vault_path, entry):
    entry_rel = entry.get("entry") or entry.get("note", "")
    entry_abs = _resolve_entry_path(vault_path, entry_rel, entry.get("channel", "my-portfolio"))
    parsed = _parse_entry(entry_abs) if entry_abs else {
        "themes": [], "abstract": "", "summary": "", "one_liner": "",
    }
    dd_path = os.path.join(vault_path, "builder/deepdives", entry["slug"] + ".md")
    profile = entry.get("profile", "portfolio")

    charted = (
        _themes_complete(entry.get("themes"), parsed["themes"])
        and _abstract_complete(parsed, profile)
        and _one_complete(entry.get("one", ""), parsed["one_liner"])
    )
    processed = charted and _deepdive_complete(dd_path, profile)

    registry_status = entry.get("status") or ""
    if registry_status == "quick-dip" and not processed:
        if charted:
            status = "needs_deep_dive"
        else:
            status = "quick_dip"
    elif processed:
        status = "processed"
    elif charted:
        status = "needs_deep_dive"
    else:
        status = "scaffolded"

    return {
        "slug": entry["slug"],
        "title": entry.get("title", entry["slug"]),
        "channel": entry.get("channel"),
        "profile": profile,
        "status": status,
        "has_deepdive": os.path.exists(dd_path),
    }


def assess_channel(vault_path, channel_id, pending_count=0):
    corpus = [e for e in load_corpus(vault_path) if e.get("channel") == channel_id]
    assessed = [assess_entry(vault_path, e) for e in corpus]
    counts = {"pending": pending_count, "on_chart": len(corpus),
              "quick_dip": 0, "needs_deep_dive": 0, "scaffolded": 0, "processed": 0,
              "charted": 0}
    needs_attention = []
    for a in assessed:
        counts[a["status"]] += 1
        if a["status"] in ("scaffolded", "needs_deep_dive", "charted"):
            needs_attention.append(a)
    return {"counts": counts, "entries": assessed, "needs_attention": needs_attention}


def assess_vault(vault_path, channel_pending=None):
    channel_pending = channel_pending or {}
    corpus = load_corpus(vault_path)
    all_assessed = [assess_entry(vault_path, e) for e in corpus]
    totals = {"on_chart": len(corpus), "pending": sum(channel_pending.values()),
              "quick_dip": 0, "needs_deep_dive": 0, "scaffolded": 0, "processed": 0, "charted": 0}
    for a in all_assessed:
        totals[a["status"]] += 1
    by_channel = {}
    channels = set(e.get("channel") for e in corpus) | set(channel_pending.keys())
    for ch in channels:
        by_channel[ch] = assess_channel(vault_path, ch, channel_pending.get(ch, 0))
    return {"totals": totals, "by_channel": by_channel, "entries": all_assessed}
