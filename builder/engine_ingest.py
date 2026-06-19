#!/usr/bin/env python3
"""Build deterministic wiki/sources pages from docked ingest-channel entries."""
import os
import re
import datetime


def _read_entry(entry_path):
    if not os.path.exists(entry_path):
        return ""
    with open(entry_path) as f:
        lines = f.readlines()
    out, started = [], False
    for ln in lines:
        s = ln.rstrip("\n")
        if not started:
            if s.strip().startswith("<!--"):
                continue
            if re.match(r"^\s*(\[\[.*\]\][,\s]*)+$", s.strip()):
                started = True
                continue
            if s.strip() == "":
                continue
            started = True
        out.append(s)
    return "\n".join(out).strip()


def _source_slug(entry):
    d = entry.get("date_ingested") or datetime.date.today().isoformat()
    return "{}-{}".format(d, entry["slug"])


def _patch_index(root, sources, today):
    index_path = os.path.join(root, "index.md")
    if not os.path.exists(index_path):
        return
    with open(index_path) as f:
        text = f.read()
    marker = "## Docked artifacts"
    if marker in text:
        text = text.split(marker)[0].rstrip()
    if not sources:
        with open(index_path, "w") as f:
            f.write(text.rstrip() + "\n")
        return
    lines = ["", marker, "",
             "Deterministic chart entries from dock channels (not yet LLM-ingested).", ""]
    by_channel = {}
    for s in sources:
        by_channel.setdefault(s.get("channel", "ingest"), []).append(s)
    for ch, items in sorted(by_channel.items()):
        lines.append("### {}".format(ch))
        for s in sorted(items, key=lambda x: x.get("title", "")):
            wiki_slug = _source_slug(s)
            lines.append("- [[{}|{}]] — {} · _{}_".format(
                wiki_slug, s["title"], s.get("source_file", ""), s.get("status", "staged")))
        lines.append("")
    lines += ["## See also", "", "[[overview]] · [[log]] · [[CLAUDE|schema]]", ""]
    with open(index_path, "w") as f:
        f.write(text + "\n".join(lines))


def build(root, data, today, rebuild_slugs=None):
    """Create wiki/sources shells from builder/entries for ingest channels."""
    sources = list(getattr(data, "S", []))
    sources_dir = os.path.join(root, "wiki/sources")
    os.makedirs(sources_dir, exist_ok=True)

    built = 0
    for s in sources:
        slug = s["slug"]
        if rebuild_slugs is not None and slug not in rebuild_slugs:
            continue
        entry_rel = s.get("entry", "")
        entry_abs = os.path.join(root, entry_rel) if entry_rel else None
        body = _read_entry(entry_abs) if entry_abs else "*Entry pending — run Surface Interval.*"
        wiki_slug = _source_slug(s)
        title = s.get("title", slug).replace('"', "'")
        source_type = s.get("source_type", "note")
        source_file = s.get("source_file", "")

        fm = [
            "---",
            "type: source",
            'title: "{}"'.format(title),
            "source_file: {}".format(source_file),
            "source_type: {}".format(source_type),
            "channel: {}".format(s.get("channel", "")),
            "status: {}".format(s.get("status", "staged")),
            "date_ingested: {}".format(today),
            "tags: [docked]",
            "---",
            "",
            "# {}".format(s.get("title", slug)),
            "",
            "> Deterministic chart entry — generative summary via **Deep Dive** (LLM) later.",
            "",
        ]
        if s.get("flag"):
            fm += ["> [!warning] Needs attention", "> {}".format(s["flag"]), ""]
        dd_path = os.path.join(root, "builder/deepdives", slug + ".md")
        if os.path.exists(dd_path):
            with open(dd_path) as df:
                dd = df.read().strip()
        else:
            dd = "*Deep dive pending — run LLM Deep Dive or edit `builder/deepdives/{}.md`.*".format(slug)

        lines = fm + [
            "## Summary",
            "",
            body,
            "",
            "## Deep dive",
            "",
            dd,
            "",
            "## Source",
            "",
            "- `{}`".format(source_file),
            "- Chart entry: `{}`".format(entry_rel),
            "- Templates: `builder/templates/{}/entry.md`".format(s.get("channel", "")),
            "",
        ]
        out_path = os.path.join(sources_dir, wiki_slug + ".md")
        with open(out_path, "w") as f:
            f.write("\n".join(lines))
        built += 1

    _patch_index(root, sources, today)
    return {"sources": len(sources), "sources_built": built,
            "sources_skipped": len(sources) - built}
