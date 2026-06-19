#!/usr/bin/env python3
"""ENGINE (generic, do not edit per-vault): builds wiki/papers, wiki/themes, and index.md
from data.THEMES + data.P. Deep dives are injected from <builder>/deepdives/<slug>.md.
Call build(root, deepdives_dir, data, today)."""
import os, re
from collections import Counter, defaultdict

STATUS_LABEL = {"mapped": "📄 abstract + PDF",
                "no-pdf": "📝 abstract only (PDF not in raw/)",
                "inferred": "🔎 PDF only (note drafted by Claude — confirm)"}
ICON = {"mapped": "📄", "no-pdf": "📝", "inferred": "🔎"}


def _read_body(abs_dir, note_fn):
    with open(os.path.join(abs_dir, note_fn)) as f:
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
    body = "\n".join(out).strip()
    body = re.sub(r"^\s*#{1,6}\s*Abstract\s*:?\s*\n+", "", body, count=1, flags=re.IGNORECASE)
    return body.strip()


def build(root, deepdives_dir, data, today):
    THEMES, P = data.THEMES, data.P
    abs_dir = os.path.join(root, "raw/notes/recent project abstracts")
    papers_dir = os.path.join(root, "wiki/papers")
    themes_dir = os.path.join(root, "wiki/themes")
    os.makedirs(papers_dir, exist_ok=True)
    os.makedirs(themes_dir, exist_ok=True)

    def theme_links(slugs):
        return ", ".join(f"[[{s}|{THEMES[s][0]}]]" for s in slugs)

    # ---- paper pages ----
    for p in P:
        body = _read_body(abs_dir, p["note"])
        fm = ["---", "type: paper", f'title: "{p["title"].replace(chr(34), chr(39))}"', f"slug: {p['slug']}",
              f"venue: {p['venue']}", f"year: {p['year']}", f"status: {p['status']}",
              "themes: [" + ", ".join(p["themes"]) + "]",
              "pdfs: [" + ", ".join(f'"raw/papers/{x}"' for x in p["pdfs"]) + "]",
              f"updated: {today}", "---", ""]
        lines = fm + [f"# {p['title']}", "", f"> {p['one']}", "",
                      f"**Venue:** {p['venue']} · **Year:** {p['year']} · **Source:** {STATUS_LABEL[p['status']]}", "",
                      f"**Themes:** {theme_links(p['themes'])}", ""]
        if p.get("flag"):
            lines += [f"> [!warning] Needs confirmation\n> {p['flag']}", ""]
        dd_path = os.path.join(deepdives_dir, p["slug"] + ".md")
        if os.path.exists(dd_path):
            with open(dd_path) as df:
                dd = df.read().strip()
        elif p["status"] == "no-pdf":
            dd = "*No PDF in `raw/papers/` yet — deep dive pending. Abstract/notes above stand in for now.*"
        else:
            dd = "*Deep dive pending — will be filled from the PDF.*"
        lines += ["## Abstract / Notes", "", body, "", "## Deep dive", "", dd, "", "## Source", ""]
        if p["pdfs"]:
            for x in p["pdfs"]:
                lines.append(f"- `raw/papers/{x}`")
        else:
            lines.append("- *(PDF not present in `raw/papers/` yet.)*")
        lines.append(f"- Abstract note: `raw/notes/recent project abstracts/{p['note']}`")
        with open(os.path.join(papers_dir, p["slug"] + ".md"), "w") as f:
            f.write("\n".join(lines) + "\n")

    # ---- co-occurrence + theme pages ----
    cooc = defaultdict(Counter)
    papers_by_theme = defaultdict(list)
    for p in P:
        for t in p["themes"]:
            papers_by_theme[t].append(p)
        for a in p["themes"]:
            for b in p["themes"]:
                if a != b:
                    cooc[a][b] += 1

    for slug, (name, core, has_note) in THEMES.items():
        ps = sorted(papers_by_theme.get(slug, []), key=lambda x: (-x["year"], x["title"]))
        lines = ["---", "type: theme", f'title: "{name}"', f"slug: {slug}",
                 f"paper_count: {len(ps)}", f"updated: {today}", "---", "",
                 f"# {name}", "", f"> **Core idea:** {core}", ""]
        if not has_note:
            lines += ["> [!note] Inferred theme\n> Referenced by your abstract notes but without a theme note of its own yet. Core idea drafted by Claude — please confirm or replace.", ""]
        else:
            lines += [f"*Source note:* `raw/notes/research themes/{name}.md`", ""]
        lines += [f"## Papers ({len(ps)})", ""]
        for p in ps:
            tag = "" if p["status"] == "mapped" else (" _(abstract only)_" if p["status"] == "no-pdf" else " _(drafted note)_")
            lines.append(f"- [[{p['slug']}|{p['title']}]] — {p['venue']} {p['year']}.{tag} {p['one']}")
        rel = [b for b, _ in cooc[slug].most_common(5)]
        if rel:
            lines += ["", "## Related themes", ""]
            lines.append(", ".join(f"[[{b}|{THEMES[b][0]}]] ({cooc[slug][b]})" for b in rel))
        lines += ["", "## See also", "", "[[overview|Portfolio overview]] · [[index]]"]
        with open(os.path.join(themes_dir, slug + ".md"), "w") as f:
            f.write("\n".join(lines) + "\n")

    # ---- index.md ----
    n_mapped = sum(1 for p in P if p["status"] == "mapped")
    n_nopdf = sum(1 for p in P if p["status"] == "no-pdf")
    n_inf = sum(1 for p in P if p["status"] == "inferred")
    idx = ["---", "type: index", f"updated: {today}", "---", "", "# Index", "",
           " A catalog of the research-portfolio map. **Read this first** to navigate, then open a [[overview|portfolio overview]] for the cross-cutting threads.", "",
           f"**Totals:** {len(P)} papers ({n_mapped} with PDF, {n_nopdf} abstract-only, {n_inf} drafted-from-PDF) · {len(THEMES)} themes", "",
           "**Legend:** 📄 abstract+PDF · 📝 abstract only (PDF not in `raw/`) · 🔎 PDF only (note drafted by Claude, theme inferred — pending confirmation)", "",
           "---", "", "## Research themes", ""]
    for slug, (name, core, has_note) in sorted(THEMES.items(), key=lambda kv: -len(papers_by_theme.get(kv[0], []))):
        n = len(papers_by_theme.get(slug, []))
        extra = "" if has_note else " _(inferred theme — confirm)_"
        idx.append(f"- [[{slug}|{name}]] ({n}) — {core}{extra}")
    idx += ["", "## Papers by year", ""]
    for yr in sorted({p["year"] for p in P}, reverse=True):
        idx.append(f"### {yr}")
        for p in sorted([x for x in P if x["year"] == yr], key=lambda x: x["title"]):
            idx.append(f"- {ICON[p['status']]} [[{p['slug']}|{p['title']}]] — {p['venue']} {p['year']}. {p['one']}")
        idx.append("")
    idx += ["## See also", "", "[[overview|Portfolio overview]] · [[log]] · [[CLAUDE|schema]]"]
    with open(os.path.join(root, "index.md"), "w") as f:
        f.write("\n".join(idx) + "\n")

    return {"papers": len(P), "themes": len(THEMES),
            "no-pdf": [p["slug"] for p in P if p["status"] == "no-pdf"],
            "inferred": [p["slug"] for p in P if p["status"] == "inferred"]}
