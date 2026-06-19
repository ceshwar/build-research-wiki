#!/usr/bin/env python3
"""Helpers for incremental wiki builds — skip unchanged paper/theme/concept pages."""
import os


def _mtime(path):
    return os.path.getmtime(path) if os.path.exists(path) else 0.0


def _max_mtime(paths):
    return max((_mtime(p) for p in paths), default=0.0)


def _notes_dirs(data):
    notes = getattr(data, "NOTES", {})
    return {
        "abstracts": notes.get("abstracts", "raw/notes/abstracts"),
        "themes": notes.get("themes", "raw/notes/themes"),
    }


def _note_path(root, p, notes_dirs):
    rel = p["note"]
    if "/" not in rel and not rel.startswith("raw/"):
        rel = os.path.join(notes_dirs["abstracts"], rel)
    return os.path.join(root, rel.replace("\\", "/"))


def _theme_note_path(root, slug, notes_dirs):
    return os.path.join(root, notes_dirs["themes"], slug + ".md")


def wiki_exists(root):
    papers_dir = os.path.join(root, "wiki/papers")
    if not os.path.isdir(papers_dir):
        return False
    return any(f.endswith(".md") for f in os.listdir(papers_dir))


def plan(root, data_path, deepdives_dir, data):
    """Return (rebuild_papers, rebuild_themes) as sets of slugs needing refresh."""
    notes_dirs = _notes_dirs(data)
    data_mtime = _mtime(data_path)
    rebuild_papers = set()

    for p in data.P:
        out = os.path.join(root, "wiki/papers", p["slug"] + ".md")
        inputs = [data_path, _note_path(root, p, notes_dirs)]
        for pdf in p.get("pdfs", []):
            inputs.append(os.path.join(root, "raw/papers", pdf))
        dd = os.path.join(deepdives_dir, p["slug"] + ".md")
        if os.path.exists(dd):
            inputs.append(dd)

        if not os.path.exists(out) or _max_mtime(inputs) > _mtime(out):
            rebuild_papers.add(p["slug"])

    papers_by_theme = {}
    for p in data.P:
        for t in p.get("themes", []):
            papers_by_theme.setdefault(t, []).append(p)

    rebuild_themes = set()
    for slug in data.THEMES:
        out = os.path.join(root, "wiki/themes", slug + ".md")
        theme_inputs = [data_path, _theme_note_path(root, slug, notes_dirs)]
        touched = any(p["slug"] in rebuild_papers for p in papers_by_theme.get(slug, []))

        if touched or not os.path.exists(out) or _max_mtime(theme_inputs) > _mtime(out):
            rebuild_themes.add(slug)

    return rebuild_papers, rebuild_themes


def unmapped_pdfs(root, data):
    """PDFs in raw/papers/ not referenced by any row in data.P (+ auto)."""
    papers_dir = os.path.join(root, "raw/papers")
    if not os.path.isdir(papers_dir):
        return []
    known = set()
    for p in data.P:
        for pdf in p.get("pdfs", []):
            known.add(pdf)
            known.add(os.path.basename(pdf))
    return sorted(
        f for f in os.listdir(papers_dir)
        if f.lower().endswith(".pdf") and f not in known
    )
