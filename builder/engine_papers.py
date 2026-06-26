#!/usr/bin/env python3
"""ENGINE (generic, do not edit per-vault): builds wiki/papers, wiki/themes, and index.md
from data.THEMES + data.P. Deep dives are injected from <builder>/deepdives/<slug>.md.
Call build(root, deepdives_dir, data, today)."""
import os, re
from collections import Counter, defaultdict

STATUS_LABEL = {
    "mapped": "deep dive",
    "no-pdf": "uncharted (no PDF)",
    "inferred": "legacy",
    "quick-dip": "uncharted (PDF surfaced)",
}
ICON = {"mapped": "🦑", "no-pdf": "◎", "inferred": "○", "quick-dip": "◎"}


def _display_field(val, empty="—"):
    if val is None or val == "" or val == 0:
        return empty
    return str(val)


def _display_venue(p):
    venue = p.get("venue") or ""
    if p.get("preprint") or (venue.lower() == "arxiv"):
        aid = p.get("arxiv_id") or ""
        label = "arXiv (preprint)"
        if aid:
            label = "arXiv (preprint) · {}".format(aid)
        return label
    return _display_field(venue)


def _tier_icon(root, p):
    try:
        import verification
        vf = verification.effective(
            p, None, verification.load_overrides(os.path.join(root, "builder")))
        if vf.get("human_verified"):
            return "🦑"
        if vf.get("llm_enriched"):
            return "🤿"
    except ImportError:
        pass
    return ICON.get(p.get("status"), "◎")


def _read_theme_note_excerpt(root, slug, notes_dirs, limit=1200):
    path = _theme_note_path(root, slug, notes_dirs)
    if not os.path.isfile(path):
        return ""
    with open(path) as f:
        lines = f.readlines()
    body = []
    past_core = False
    for ln in lines:
        s = ln.rstrip("\n")
        if s.strip().startswith("**Core idea:**"):
            past_core = True
            continue
        if not past_core:
            continue
        if s.strip().startswith("## "):
            break
        if s.strip():
            body.append(s)
    text = "\n".join(body).strip()
    return text[:limit]


def _deepdive_block(p, dd_path):
    if os.path.exists(dd_path):
        with open(dd_path) as df:
            text = df.read().strip()
        if text and "chart-tier: quick-dip" not in text:
            try:
                from completion import _deepdive_complete
                if _deepdive_complete(dd_path, "portfolio"):
                    return text
                if len(text) > 80 and "(fill in" not in text.lower():
                    return text
            except ImportError:
                if len(text) > 80:
                    return text
    if p.get("status") == "no-pdf":
        return "*No PDF in `raw/papers/` yet.*"
    return "*Run **Quick Dip** (LLM) in Portolan, then review to promote to **Deep dive**.*"


def _notes_dirs(data):
    """Legacy raw note folders; override in data.NOTES."""
    notes = getattr(data, "NOTES", {})
    return {
        "abstracts": notes.get("abstracts", "raw/notes/abstracts"),
        "themes": notes.get("themes", "raw/notes/themes"),
        "entries": notes.get("entries", "builder/entries"),
    }


def _entry_path(root, p, notes_dirs):
    """Resolve chart entry file. Prefer p['entry']; fall back to legacy p['note']."""
    rel = p.get("entry") or p.get("note")
    if not rel:
        return None
    rel = rel.replace("\\", "/")
    if rel.startswith("builder/"):
        return os.path.join(root, rel)
    if "/" not in rel and not rel.startswith("raw/"):
        channel = p.get("channel", "my-portfolio")
        rel = os.path.join(notes_dirs["entries"], channel, rel)
        if not rel.endswith(".md"):
            rel += ".md"
    return os.path.join(root, rel)


def _note_path(root, p, notes_dirs):
    """Legacy abstract note path (raw/notes/abstracts). Used when no builder/entries file."""
    rel = p.get("note", "")
    if not rel or rel.startswith("builder/"):
        return _entry_path(root, p, notes_dirs)
    if "/" not in rel and not rel.startswith("raw/"):
        rel = os.path.join(notes_dirs["abstracts"], rel)
    return os.path.join(root, rel.replace("\\", "/"))


def _theme_note_path(root, slug, notes_dirs):
    return os.path.join(root, notes_dirs["themes"], slug + ".md")


def _read_body(note_path):
    if not note_path or not os.path.exists(note_path):
        return ""
    with open(note_path) as f:
        lines = f.readlines()
    out, started = [], False
    in_abstract = False
    for ln in lines:
        s = ln.rstrip("\n")
        if not started:
            if s.strip().startswith("<!--"):
                continue
            if re.match(r"^\s*(\[\[.*\]\][,\s]*)+$", s.strip()):
                continue
            if re.match(r"^\s*#{1,6}\s*Abstract\s*:?\s*$", s.strip(), re.I):
                in_abstract = True
                started = True
                continue
            if s.strip() == "":
                continue
            if s.strip().startswith("## ") and not re.match(r"^\s*##\s*Abstract", s, re.I):
                break
            started = True
        if in_abstract and s.strip().startswith("## ") and not re.match(r"^\s*##\s*Abstract", s, re.I):
            break
        out.append(s)
    body = "\n".join(out).strip()
    body = re.sub(r"^\s*#{1,6}\s*Abstract\s*:?\s*\n+", "", body, count=1, flags=re.IGNORECASE)
    return body.strip()


def _entry_meta(note_path, fallback_one, registry_themes):
    """Pull one-liner and themes from builder/entries when present."""
    themes = list(registry_themes or [])
    one = fallback_one
    if not note_path or not os.path.exists(note_path):
        return one, themes
    try:
        from completion import _parse_entry, _one_complete
        parsed = _parse_entry(note_path)
        if parsed["themes"]:
            themes = parsed["themes"]
        if _one_complete(fallback_one, parsed["one_liner"]):
            one = parsed["one_liner"] or fallback_one
    except ImportError:
        pass
    return one, themes


def build(root, deepdives_dir, data, today, rebuild_papers=None, rebuild_themes=None):
    """Build paper + theme pages. If rebuild_* sets are given, skip unchanged slugs."""
    THEMES, P = data.THEMES, data.P
    notes_dirs = _notes_dirs(data)
    papers_dir = os.path.join(root, "wiki/papers")
    themes_dir = os.path.join(root, "wiki/themes")
    os.makedirs(papers_dir, exist_ok=True)
    os.makedirs(themes_dir, exist_ok=True)

    def pdf_display(pdf):
        if "/" in pdf or pdf.startswith("raw/"):
            return pdf.replace("\\", "/")
        return "raw/papers/" + pdf

    def should_rebuild_paper(slug):
        return rebuild_papers is None or slug in rebuild_papers

    def should_rebuild_theme(slug):
        return rebuild_themes is None or slug in rebuild_themes

    def theme_links(slugs):
        return ", ".join(f"[[{s}|{THEMES[s][0]}]]" for s in slugs)

    papers_built = 0
    themes_built = 0

    # ---- paper pages ----
    for p in P:
        if not should_rebuild_paper(p["slug"]):
            continue
        papers_built += 1
        note_abs = _note_path(root, p, notes_dirs)
        note_rel = os.path.relpath(note_abs, root).replace("\\", "/") if note_abs and os.path.exists(note_abs) else p.get("entry", "")
        body = _read_body(note_abs) if note_abs and os.path.exists(note_abs) else ""
        one_line, theme_slugs = _entry_meta(note_abs, p.get("one", ""), p.get("themes", []))
        venue = _display_field(p.get("venue"))
        year = _display_field(p.get("year"))
        vf = None
        try:
            import verification
            vf = verification.effective(
                p, None, verification.load_overrides(os.path.join(root, "builder")))
        except ImportError:
            pass
        fm = ["---", "type: paper", f'title: "{p["title"].replace(chr(34), chr(39))}"', f"slug: {p['slug']}",
              f"venue: {p.get('venue') or ''}", f"year: {p.get('year') or 0}", f"status: {p['status']}"]
        if p.get("preprint"):
            fm.append("preprint: true")
        if p.get("arxiv_id"):
            fm.append(f"arxiv_id: {p['arxiv_id']}")
        if vf is not None:
            fm += [
                f"human_verified: {'true' if vf['human_verified'] else 'false'}",
                f"llm_enriched: {'true' if vf['llm_enriched'] else 'false'}",
                f"enrichment_source: {vf.get('enrichment_source') or 'human'}",
                f"territory: {vf.get('territory') or 'charted'}",
            ]
        fm += [
              "themes: [" + ", ".join(theme_slugs) + "]",
              "pdfs: [" + ", ".join('"{}"'.format(pdf_display(x)) for x in p["pdfs"]) + "]",
              f"updated: {today}", "---", ""]
        one_display = one_line if one_line else "—"
        lines = fm + [f"# {p['title'] or p['slug']}", "", f"> {one_display}", ""]
        if vf and vf.get("llm_enriched") and not vf.get("human_verified"):
            model = vf.get("llm_model") or "LLM"
            lines += [
                f"> [!note] Quick dip — needs review\n"
                f"> LLM-ingested ({model}). Mark **verified** in Portolan after review to promote to **Deep dive**.",
                "",
            ]
        elif vf and vf.get("human_verified"):
            by = vf.get("verified_by") or "reviewer"
            when = f" on {vf['verified_at']}" if vf.get("verified_at") else ""
            lines += [f"> [!tip] Deep dive\n> Verified by {by}{when}.", ""]
        elif not vf or not vf.get("llm_enriched"):
            if p.get("status") == "quick-dip":
                lines += [
                    "> [!note] Uncharted\n"
                    "> PDF surfaced on chart. Run **Quick Dip** (LLM) in Portolan when ready.",
                    "",
                ]
            elif p.get("status") == "no-pdf":
                lines += ["> [!note] Uncharted\n> Entry on chart — add a PDF or run Quick Dip.", ""]
        dd_path = os.path.join(deepdives_dir, p["slug"] + ".md")
        dd = _deepdive_block(p, dd_path)
        abstract_section = body if body else "—"
        lines += ["## Abstract / Notes", "", abstract_section, "", "## Deep dive", "", dd, "", "## Source", ""]
        if p["pdfs"]:
            for x in p["pdfs"]:
                lines.append("- `{}`".format(pdf_display(x)))
        else:
            lines.append("- *(PDF not present in `raw/papers/` yet.)*")
        if note_rel:
            label = "Chart entry" if note_rel.startswith("builder/entries") else "Legacy note"
            lines.append("- {}: `{}`".format(label, note_rel))
        with open(os.path.join(papers_dir, p["slug"] + ".md"), "w") as f:
            f.write("\n".join(lines) + "\n")

    # ---- co-occurrence + theme pages ----
    cooc = defaultdict(Counter)
    papers_by_theme = defaultdict(list)
    for p in P:
        note_abs = _note_path(root, p, notes_dirs)
        _, theme_slugs = _entry_meta(note_abs, p.get("one", ""), p.get("themes", []))
        for t in theme_slugs:
            papers_by_theme[t].append(p)
        for a in theme_slugs:
            for b in theme_slugs:
                if a != b:
                    cooc[a][b] += 1

    for slug, (name, core, has_note) in THEMES.items():
        if not should_rebuild_theme(slug):
            continue
        themes_built += 1
        ps = sorted(papers_by_theme.get(slug, []), key=lambda x: (-x["year"], x["title"]))
        theme_rel = os.path.relpath(_theme_note_path(root, slug, notes_dirs), root).replace("\\", "/")
        lines = ["---", "type: theme", f'title: "{name}"', f"slug: {slug}",
                 f"paper_count: {len(ps)}", f"updated: {today}", "---", "",
                 f"# {name}", "", f"> **Core idea:** {core}", ""]
        if not has_note:
            lines += [
                "> [!note] Inferred theme\n"
                "> Referenced in abstract notes but no dedicated theme note yet. "
                "Add `raw/notes/themes/{}.md` with a **Core idea:** line.".format(slug),
                "",
            ]
        else:
            excerpt = _read_theme_note_excerpt(root, slug, notes_dirs)
            if excerpt:
                lines += ["## Notes", "", excerpt, ""]
            lines += [f"*Theme note:* `{theme_rel}`", ""]
        lines += [f"## Papers ({len(ps)})", ""]
        if not ps:
            lines += ["*No papers charted under this theme yet.*", ""]
        for p in ps:
            icon = _tier_icon(root, p)
            venue = _display_venue(p)
            year = _display_field(p.get("year"))
            one = (p.get("one") or "").strip()
            meta = " · ".join(x for x in (venue, year) if x and x != "—")
            suffix = f" — {one}" if one else ""
            lines.append(f"- {icon} [[{p['slug']}|{p['title']}]] · {meta}{suffix}")
        rel = [b for b, _ in cooc[slug].most_common(5)]
        if rel:
            lines += ["", "## Related themes", ""]
            lines.append(", ".join(f"[[{b}|{THEMES[b][0]}]] ({cooc[slug][b]})" for b in rel))
        lines += ["", "## See also", "", "[[overview|Portfolio overview]] · [[index]]"]
        with open(os.path.join(themes_dir, slug + ".md"), "w") as f:
            f.write("\n".join(lines) + "\n")

    # ---- index.md ----
    n_mapped = sum(1 for p in P if p["status"] == "mapped")
    n_quick = sum(1 for p in P if p["status"] == "quick-dip")
    n_nopdf = sum(1 for p in P if p["status"] == "no-pdf")
    n_inf = sum(1 for p in P if p["status"] == "inferred")
    idx = ["---", "type: index", f"updated: {today}", "---", "", "# Index", "",
           " A catalog of the research-portfolio map. **Read this first** to navigate, then open a [[overview|portfolio overview]] for the cross-cutting threads.", "",
           f"**Totals:** {len(P)} papers ({n_mapped} deep dive, {n_quick} uncharted, {n_nopdf} no PDF, {n_inf} legacy) · {len(THEMES)} themes", "",
           "**Legend:** 🦑 deep dive · ◎ uncharted · 📝 no PDF · ○ legacy", "",
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
            "papers_built": papers_built, "themes_built": themes_built,
            "papers_skipped": len(P) - papers_built,
            "themes_skipped": len(THEMES) - themes_built,
            "no-pdf": [p["slug"] for p in P if p["status"] == "no-pdf"],
            "inferred": [p["slug"] for p in P if p["status"] == "inferred"]}
