#!/usr/bin/env python3
"""Grounding helpers for Portolan LLM output — strip leaks, validate evidence & links."""

import difflib
import glob
import json
import os
import re

from slug_util import canonical_slug

# Qwen3 may leak reasoning even with think=false (see manager/scripts/.llm-compare/).
def _thinking_patterns():
    tags = ("think", "redacted_thinking")
    pats = [
        re.compile(r"<{t}>.*?</{t}>".format(t=tag), re.DOTALL | re.IGNORECASE)
        for tag in tags
    ]
    pats.append(re.compile(r"^.*?</think>\s*", re.DOTALL | re.IGNORECASE))
    return pats


_THINKING_PATTERNS = _thinking_patterns()


def sanitize_llm_output(text):
    """Remove model reasoning blocks before parse or write."""
    if not text:
        return ""
    out = text
    for pat in _THINKING_PATTERNS:
        out = pat.sub("", out)
    return out.strip()


def _normalize_ws(s):
    return re.sub(r"\s+", " ", (s or "").lower().strip())


def evidence_grounds(span, source_text, min_ratio=0.72):
    """True when span is a (fuzzy) substring of source_text."""
    if not span or not source_text:
        return False
    span_n = _normalize_ws(span)
    src_n = _normalize_ws(source_text)
    if len(span_n) < 8:
        return span_n in src_n
    if span_n in src_n:
        return True
    window = min(len(span_n) + 40, len(src_n))
    step = max(16, window // 5)
    best = 0.0
    for i in range(0, max(1, len(src_n) - window + 1), step):
        chunk = src_n[i : i + window]
        ratio = difflib.SequenceMatcher(None, span_n, chunk).ratio()
        if ratio > best:
            best = ratio
        if best >= min_ratio:
            return True
    return best >= min_ratio


def load_resolving_slugs(vault):
    """Wiki slugs that resolve in build.py link_check (basename without .md)."""
    root = os.path.abspath(vault)
    files = set()
    for pattern in (os.path.join(root, "wiki", "**", "*.md"), os.path.join(root, "*.md")):
        for path in glob.glob(pattern, recursive=True):
            files.add(os.path.splitext(os.path.basename(path))[0])
    return files


def load_allowed_theme_slugs(vault):
    data_path = os.path.join(vault, "builder", "data.py")
    if not os.path.isfile(data_path):
        return set()
    import importlib.util

    spec = importlib.util.spec_from_file_location("_portolan_data", data_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return set(getattr(mod, "THEMES", {}).keys())


def sanitize_wikilinks(text, allowed_slugs):
    """Keep only resolving [[wikilinks]]; return plain text for unknown targets."""
    proposed = []

    def repl(match):
        raw = match.group(1)
        target = raw.split("|")[0].split("\\")[0].strip()
        slug = canonical_slug(target) or target.lower()
        if slug in allowed_slugs:
            return match.group(0)
        proposed.append(slug)
        display = raw.split("|")[-1].strip() if "|" in raw else target
        return display

    out = re.sub(r"\[\[([^\]]+)\]\]", repl, text or "")
    return out, proposed


def filter_themes(themes, allowed_theme_slugs):
    out = []
    for raw in themes or []:
        slug = canonical_slug(str(raw).strip()) or str(raw).strip().lower()
        if slug in allowed_theme_slugs and slug not in out:
            out.append(slug)
    return out


def locked_metadata(item):
    """Deterministic facts from registry / Quick Dip — LLM must not override."""
    locked = {}
    if item.get("title"):
        locked["title"] = item["title"]
    if item.get("venue"):
        locked["venue"] = item["venue"]
    if item.get("year"):
        locked["year"] = item["year"]
    authors = item.get("authors")
    if authors:
        locked["authors"] = authors if isinstance(authors, list) else [authors]
    return locked


def format_locked_block(locked):
    if not locked:
        return ""
    lines = ["**LOCKED METADATA** (do not contradict or invent alternatives):"]
    if locked.get("title"):
        lines.append(f"- Title: {locked['title']}")
    if locked.get("venue"):
        lines.append(f"- Venue: {locked['venue']}")
    if locked.get("year"):
        lines.append(f"- Year: {locked['year']}")
    if locked.get("authors"):
        auth = locked["authors"]
        if isinstance(auth, list):
            lines.append(f"- Authors: {', '.join(auth)}")
        else:
            lines.append(f"- Authors: {auth}")
    return "\n".join(lines)


def authors_section_text(locked, llm_text):
    """Prefer locked authors; append venue/year when known."""
    parts = []
    if locked.get("authors"):
        parts.append(", ".join(locked["authors"]) if isinstance(locked["authors"], list) else str(locked["authors"]))
    elif llm_text:
        parts.append(llm_text.strip())
    meta = []
    if locked.get("venue"):
        meta.append(str(locked["venue"]))
    if locked.get("year"):
        meta.append(str(locked["year"]))
    if meta and parts:
        parts.append(" · ".join(meta))
    elif meta:
        parts.append(" · ".join(meta))
    return "\n\n".join(parts) if parts else (llm_text or "").strip()


def save_proposed_links(builder_dir, channel_id, slug, proposed):
    if not proposed:
        return None
    out_dir = os.path.join(builder_dir, "proposed_links", channel_id)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, slug + ".json")
    unique = sorted(set(proposed))
    with open(path, "w") as f:
        json.dump({"slug": slug, "channel": channel_id, "proposed": unique}, f, indent=2)
        f.write("\n")
    return path


def assemble_deep_dive_body(sections, allowed_slugs):
    """Build markdown deep dive from validated section dicts."""
    lines = []
    for sec in sections:
        name = sec.get("name", "").strip()
        text = sec.get("text", "").strip()
        if not name or not text:
            continue
        text, _props = sanitize_wikilinks(text, allowed_slugs)
        lines.append(f"**{name}.**  ")
        lines.append(text)
        lines.append("")
    return "\n".join(lines).strip()
