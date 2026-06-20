#!/usr/bin/env python3
"""Generate a ready-to-paste ingest prompt for a coding agent (Claude Code / Cursor).

The "Manual agent" ingest model: SCUBA does the deterministic Quick Dip; the actual
LLM enrichment is done by the vault owner's own agent. This module surfaces exactly
which docked artifacts still need work, what is missing on each, and the precise files
to write — grounded in CLAUDE.md — so the user can paste one prompt and let the agent
fill the Deep Dives (portfolio) or full source pages (ingest docks).

    python3 builder/ingest_prompt.py --vault /path/to/vault --channel my-portfolio
"""
import os
import sys

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))
if BUILDER_DIR not in sys.path:
    sys.path.insert(0, BUILDER_DIR)

import completion
import registry
from docks_util import load_channel_map

# Deep-dive sections the agent should fill, per dock profile (mirrors completion.py).
PORTFOLIO_SECTIONS = [
    "Authors", "Research question", "Method", "Findings",
    "Claims & evidence", "Limitations", "Contributes to",
]
INGEST_SECTIONS = [
    "Authors", "Research question", "Method", "Findings",
    "Claims & evidence", "Limitations", "Relevance to my review",
]

# Statuses that still need an agent pass (anything short of a finished page).
NEEDS_WORK = ("quick_dip", "needs_deep_dive", "scaffolded")


def _full_corpus(vault):
    """Like completion.load_corpus but retains source paths (pdfs / source_file)."""
    builder = os.path.join(vault, "builder")
    items = []
    data_path = os.path.join(builder, "data.py")
    if os.path.exists(data_path):
        data = completion._load_module(data_path)
        for p in getattr(data, "P", []):
            channel = p.get("channel") or (
                "lab-portfolio" if any("lab/" in x for x in p.get("pdfs", [])) else "my-portfolio")
            items.append({**p, "profile": "portfolio", "channel": channel})
        for s in getattr(data, "S", []):
            items.append({**s, "profile": "ingest", "channel": s.get("channel", "lit-review")})

    for json_name, profile, default_channel in [
        ("auto_papers.json", "portfolio", "my-portfolio"),
        ("auto_lab_papers.json", "portfolio", "lab-portfolio"),
        ("auto_sources.json", "ingest", None),
    ]:
        for item in registry.load(builder, json_name):
            channel = item.get("channel") or default_channel
            items.append({**item, "profile": profile, "channel": channel})
    return items


def _source_path(vault, item, channels):
    """Vault-relative path to the artifact in raw/ (best effort)."""
    if item.get("source_file"):
        return item["source_file"]
    pdfs = item.get("pdfs") or []
    if not pdfs:
        return ""
    src = pdfs[0]
    if "/" not in src:
        raw_path = channels.get(item["channel"], {}).get("raw_path", "raw/papers")
        src = "{}/{}".format(raw_path, src)
    return src


def _missing(vault, item):
    """Which pieces of a chart entry are still empty, in agent-actionable terms."""
    profile = item.get("profile", "portfolio")
    entry_rel = item.get("entry") or item.get("note", "")
    entry_abs = completion._resolve_entry_path(vault, entry_rel, item.get("channel", "my-portfolio"))
    parsed = completion._parse_entry(entry_abs) if entry_abs else {
        "themes": [], "abstract": "", "summary": "", "one_liner": ""}
    dd_path = os.path.join(vault, "builder/deepdives", item["slug"] + ".md")

    missing = []
    if profile == "portfolio" and not completion._themes_complete(item.get("themes"), parsed["themes"]):
        missing.append("theme `[[links]]` on line 1 of the entry")
    if not completion._one_complete(item.get("one", ""), parsed["one_liner"]):
        missing.append("a one-line contribution (`## One-liner`)")
    if not completion._abstract_complete(parsed, profile):
        label = "summary" if profile == "ingest" else "abstract"
        missing.append("the {} (`## {}`)".format(label, label.capitalize()))
    if not completion._deepdive_complete(dd_path, profile):
        missing.append("the deep dive (create/fill `builder/deepdives/{}.md`)".format(item["slug"]))
    return missing


def collect(vault, channel_id=None):
    """Return artifacts needing an agent pass, with paths and per-item missing pieces."""
    channels = load_channel_map(vault)
    out = []
    for item in _full_corpus(vault):
        if channel_id and item.get("channel") != channel_id:
            continue
        status = completion.assess_entry(vault, item)["status"]
        if status not in NEEDS_WORK:
            continue
        out.append({
            "slug": item["slug"],
            "title": item.get("title") or item["slug"],
            "channel": item.get("channel"),
            "profile": item.get("profile", "portfolio"),
            "status": status,
            "source": _source_path(vault, item, channels),
            "entry": (item.get("entry") or item.get("note", "")),
            "deepdive": "builder/deepdives/{}.md".format(item["slug"]),
            "missing": _missing(vault, item),
        })
    return out


def _load_themes(vault):
    """Return theme slugs + display titles from builder/data.py."""
    data_path = os.path.join(vault, "builder", "data.py")
    if not os.path.exists(data_path):
        return []
    data = completion._load_module(data_path)
    themes = getattr(data, "THEMES", {})
    return [{"slug": slug, "title": meta[0]} for slug, meta in sorted(themes.items())]


def build_prompt(vault, channel_id=None):
    """Render the paste-ready agent prompt. Returns (text, item_count)."""
    vault = os.path.abspath(vault)
    items = collect(vault, channel_id)
    channels = load_channel_map(vault)
    ch_name = channels.get(channel_id, {}).get("name", channel_id or "all docks")
    vault_name = os.path.basename(vault)

    if not items:
        scope = "in **{}** ".format(ch_name) if channel_id else ""
        return ("Every charted artifact {}is fully enriched — nothing needs an agent pass. "
                "Dock new files and run Quick Dip first.".format(scope), 0)

    L = []
    L.append("# Ingest task — {} · {} ({} artifact{})".format(
        vault_name, ch_name, len(items), "" if len(items) == 1 else "s"))
    L.append("")
    L.append("You are maintaining this LLM Wiki. **Read and follow `CLAUDE.md` in this vault** "
             "(esp. the page format in §4 and the INGEST rules in §6). Work faithfully from the "
             "sources — summarize, don't invent; label any outside knowledge **[external]**.")
    L.append("")
    L.append("**Rules:** Sources in `raw/` are immutable — read them, never edit them. Write only "
             "to `builder/entries/` and `builder/deepdives/`. Link liberally with `[[wikilinks]]`.")
    L.append("")
    L.append("**Read each source PDF in full** (not just the Quick Dip abstract) before writing "
             "themes, one-liners, or deep-dive sections.")
    L.append("")
    themes = _load_themes(vault)
    if themes and (not channel_id or channels.get(channel_id, {}).get("profile") == "portfolio"):
        L.append("**Allowed theme slugs** (use only these on line 1 of portfolio entries — pick 1–3 "
                 "that fit; see `wiki/themes/` for context):")
        for t in themes:
            L.append("- `[[{}]]` — {}".format(t["slug"], t["title"]))
        L.append("")
    L.append("**Vault:** `{}`".format(vault))
    L.append("")
    L.append("## Artifacts to enrich")
    L.append("")
    for i, it in enumerate(items, 1):
        sections = PORTFOLIO_SECTIONS if it["profile"] == "portfolio" else INGEST_SECTIONS
        L.append("### {}. {}".format(i, it["title"]))
        L.append("- **Status:** {} · **Dock:** {}".format(it["status"].replace("_", " "), it["channel"]))
        if it["source"]:
            L.append("- **Source (read this):** `{}`".format(it["source"]))
        L.append("- **Chart entry (edit):** `{}`".format(it["entry"]))
        L.append("- **Deep dive (create/fill):** `{}`".format(it["deepdive"]))
        if it["missing"]:
            L.append("- **Still needs:** " + "; ".join(it["missing"]) + ".")
        L.append("- **Deep-dive sections:** {}.".format(", ".join(sections)))
        L.append("")
    L.append("## When you're done")
    L.append("")
    L.append("Rebuild the chart so the pages and the Dive Computer update:")
    L.append("")
    L.append("```bash")
    L.append("python3 builder/build.py --vault {}".format(vault))
    L.append("```")
    L.append("")
    L.append("(Or click **Update chart** in SCUBA Ideaverse.)")
    return "\n".join(L), len(items)


def main():
    vault = os.path.dirname(BUILDER_DIR)
    channel_id = None
    if "--vault" in sys.argv:
        vault = os.path.abspath(sys.argv[sys.argv.index("--vault") + 1])
    if "--channel" in sys.argv:
        channel_id = sys.argv[sys.argv.index("--channel") + 1]
    text, _ = build_prompt(vault, channel_id)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
