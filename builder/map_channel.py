#!/usr/bin/env python3
"""Map docked artifacts in raw/ to chart entries (builder/entries/) — never raw/notes.

Scans a channel's raw_path, creates deterministic entry files from templates, and
updates the auto registry (auto_papers.py or auto_sources.py).

    python3 builder/map_channel.py --channel my-portfolio
    python3 builder/map_channel.py --channel lit-review --vault /path/to/vault
"""
import datetime
import os
import re
import subprocess
import sys

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BUILDER_DIR)

from templates_util import deepdive_rel_path, entry_rel_path, fill_template

CHANNELS = {
    "my-portfolio": {
        "raw_path": "raw/papers",
        "profile": "portfolio",
        "auto_file": "auto_papers.py",
        "auto_key": "P_AUTO",
        "extensions": [".pdf"],
    },
    "lab-portfolio": {
        "raw_path": "raw/lab/papers",
        "profile": "portfolio",
        "auto_file": "auto_lab_papers.py",
        "auto_key": "P_LAB_AUTO",
        "extensions": [".pdf"],
    },
    "lit-review": {
        "raw_path": "raw/literature",
        "profile": "ingest",
        "auto_file": "auto_sources.py",
        "auto_key": "S_AUTO",
        "extensions": [".pdf", ".md", ".txt"],
        "source_type": "paper",
    },
    "lab-memory": {
        "raw_path": "raw/transcripts",
        "profile": "ingest",
        "auto_file": "auto_sources.py",
        "auto_key": "S_AUTO",
        "extensions": [".txt", ".md", ".pdf", ".vtt", ".srt"],
        "source_type": "transcript",
    },
    "ideas": {
        "raw_path": "raw/notes/inbox",
        "profile": "ingest",
        "auto_file": "auto_sources.py",
        "auto_key": "S_AUTO",
        "extensions": [".md", ".txt"],
        "source_type": "note",
    },
}


def _load_data(vault):
    import importlib.util
    data_path = os.path.join(vault, "builder", "data.py")
    if not os.path.exists(data_path):
        sys.exit("No builder/data.py in vault: {}".format(vault))
    spec = importlib.util.spec_from_file_location("data", data_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, os.path.join(vault, "builder")


def _load_auto(builder_dir, auto_file, auto_key):
    auto_path = os.path.join(builder_dir, auto_file)
    if not os.path.exists(auto_path):
        return []
    import importlib.util
    spec = importlib.util.spec_from_file_location("auto_mod", auto_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return list(getattr(mod, auto_key, []))


def _known_source_files(entries, key="source_file"):
    known = set()
    for e in entries:
        if key == "pdfs":
            for sf in e.get("pdfs", []):
                if sf:
                    known.add(sf)
                    known.add(os.path.basename(sf))
            continue
        sf = e.get(key)
        if not sf:
            continue
        known.add(sf)
        known.add(os.path.basename(sf))
    return known


def _slugify(name):
    base = os.path.splitext(name)[0].lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return base or "artifact"


def _extract_pdf_title(pdf_path):
    try:
        out = subprocess.check_output(
            ["pdftotext", "-f", "1", "-l", "1", pdf_path, "-"],
            stderr=subprocess.DEVNULL,
        ).decode("utf-8", errors="replace")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return os.path.splitext(os.path.basename(pdf_path))[0].replace("_", " ").replace("-", " ")

    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    if not lines:
        return os.path.basename(pdf_path)
    title_parts = []
    for ln in lines[:6]:
        if re.search(r"(?i)abstract|introduction|keywords|copyright|doi\.org|arxiv", ln):
            break
        if re.match(r"^\d+$", ln):
            continue
        title_parts.append(ln)
        if len(" ".join(title_parts)) > 40:
            break
    title = " ".join(title_parts).strip()
    return title or lines[0]


def _guess_title(path, rel_path, ext):
    if ext == ".pdf":
        return _extract_pdf_title(path)[:200]
    if ext in (".md", ".txt"):
        try:
            with open(path) as f:
                for ln in f:
                    s = ln.strip()
                    if s.startswith("#"):
                        return s.lstrip("#").strip()[:200]
                    if s:
                        return s[:200]
        except OSError:
            pass
    return os.path.splitext(os.path.basename(path))[0].replace("_", " ").replace("-", " ")


def _guess_year(filename, title):
    m = re.search(r"(20\d{2}|19\d{2})", filename)
    if m:
        return int(m.group(1))
    m = re.search(r"(20\d{2}|19\d{2})", title)
    if m:
        return int(m.group(1))
    return datetime.date.today().year


def _write_entry(vault, channel_id, slug, title, source_file, dry_run=False):
    rel = entry_rel_path(channel_id, slug)
    if dry_run:
        return rel
    abs_path = os.path.join(vault, rel)
    if not os.path.exists(abs_path):
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        body = fill_template(channel_id, "entry", slug=slug, title=title, source_file=source_file)
        with open(abs_path, "w") as f:
            f.write(body)
    return rel


def _write_deepdive(vault, channel_id, slug, dry_run=False):
    rel = deepdive_rel_path(slug)
    if dry_run:
        return rel
    abs_path = os.path.join(vault, rel)
    if os.path.exists(abs_path):
        return rel
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    body = fill_template(channel_id, "deepdive", slug=slug)
    with open(abs_path, "w") as f:
        f.write(body)
    return rel


def _write_auto(builder_dir, entries, auto_file, auto_key, channel_id):
    path = os.path.join(builder_dir, auto_file)
    lines = [
        "# Auto-generated by builder/map_channel.py — registry only.",
        "# Edit builder/entries/{}/* for chart content; re-run Surface Interval to refresh wiki.".format(channel_id),
        "{} = [".format(auto_key),
    ]
    for e in entries:
        lines.append("    dict(")
        for key, val in e.items():
            if isinstance(val, str):
                lines.append('        {}="{}",'.format(key, val.replace('"', "'")))
            elif isinstance(val, int):
                lines.append("        {}={},".format(key, val))
            elif isinstance(val, list):
                inner = ", ".join('"{}"'.format(x) for x in val) if val else ""
                lines.append("        {}=[{}],".format(key, inner))
            elif val is None:
                lines.append("        {}=None,".format(key))
        lines.append("    ),")
    lines.append("]")
    lines.append("")
    with open(path, "w") as f:
        f.write("\n".join(lines))


def _merge_auto_sources(builder_dir, channel_id, new_entries, auto_file, auto_key):
    """Keep entries from other channels in shared auto_sources.py."""
    existing = _load_auto(builder_dir, auto_file, auto_key)
    others = [e for e in existing if e.get("channel") != channel_id]
    merged = others + new_entries
    _write_auto(builder_dir, merged, auto_file, auto_key, channel_id)


def _backfill_entries(vault, channel_id, entries, dry_run=False):
    """Migrate legacy raw/notes references to builder/entries/."""
    changed = False
    for e in entries:
        entry_rel = e.get("entry") or ""
        if entry_rel.startswith("builder/entries"):
            continue
        slug = e["slug"]
        pdfs = e.get("pdfs", [])
        rel_source = pdfs[0] if pdfs else ""
        if rel_source and "/" not in rel_source:
            cfg = CHANNELS.get(channel_id, {})
            rel_source = "{}/{}".format(cfg.get("raw_path", "raw/papers"), rel_source)
        title = e.get("title", slug)
        new_rel = _write_entry(vault, channel_id, slug, title, rel_source, dry_run)
        if not dry_run:
            _write_deepdive(vault, channel_id, slug, dry_run=False)
        e["entry"] = new_rel
        e["note"] = new_rel
        changed = True
        print("  backfill: {} → {}".format(slug, new_rel))
    return entries, changed


def map_channel(vault, channel_id, dry_run=False):
    cfg = CHANNELS.get(channel_id)
    if not cfg:
        sys.exit("Unknown channel: {}".format(channel_id))

    data, builder_dir = _load_data(vault)
    auto_file = cfg["auto_file"]
    auto_key = cfg["auto_key"]
    raw_path = cfg["raw_path"]
    profile = cfg["profile"]

    auto = _load_auto(builder_dir, auto_file, auto_key)
    if profile == "portfolio":
        channel_auto = auto if auto_file != "auto_sources.py" else [e for e in auto if e.get("channel") == channel_id]
        manual = list(data.P)
        if channel_id == "lab-portfolio":
            manual = [p for p in manual if any("lab/" in x for x in p.get("pdfs", []))]
        else:
            manual = [p for p in manual if not any("lab/" in x for x in p.get("pdfs", []))]
        channel_auto, backfilled = _backfill_entries(vault, channel_id, channel_auto, dry_run)
        if backfilled and not dry_run:
            _write_auto(builder_dir, channel_auto, auto_file, auto_key, channel_id)
        all_entries = manual + channel_auto
        known = _known_source_files(all_entries, "pdfs")
        for p in all_entries:
            for pdf in p.get("pdfs", []):
                known.add(pdf)
                known.add(os.path.basename(pdf))
    else:
        channel_auto = [e for e in auto if e.get("channel") == channel_id]
        all_entries = channel_auto
        known = _known_source_files(channel_auto)

    raw_dir = os.path.join(vault, raw_path)
    if not dry_run:
        for e in all_entries:
            _write_deepdive(vault, channel_id, e["slug"], dry_run=False)

    if not os.path.isdir(raw_dir):
        return []

    exts = set(cfg["extensions"])
    unmapped = []
    for f in sorted(os.listdir(raw_dir)):
        ext = os.path.splitext(f)[1].lower()
        if ext not in exts:
            continue
        rel = "{}/{}".format(raw_path, f).replace("\\", "/")
        if f in known or rel in known:
            continue
        unmapped.append(f)

    if not unmapped:
        return []

    new_entries = []
    existing_slugs = {e.get("slug") for e in all_entries}

    for fname in unmapped:
        fpath = os.path.join(raw_dir, fname)
        rel_source = "{}/{}".format(raw_path, fname).replace("\\", "/")
        ext = os.path.splitext(fname)[1].lower()
        title = _guess_title(fpath, rel_source, ext)
        slug = _slugify(fname)
        if channel_id != "my-portfolio" and profile == "portfolio":
            slug = channel_id.replace("-", "")[:3] + "-" + slug
        if slug in existing_slugs:
            slug = slug + "-" + str(len(existing_slugs) + len(new_entries))
        existing_slugs.add(slug)

        entry_rel = _write_entry(vault, channel_id, slug, title, rel_source, dry_run)
        if not dry_run:
            _write_deepdive(vault, channel_id, slug, dry_run=False)

        if profile == "portfolio":
            year = _guess_year(fname, title)
            pdfs = [rel_source] if channel_id != "my-portfolio" else [fname]
            entry = {
                "slug": slug,
                "entry": entry_rel,
                "note": entry_rel,
                "title": title[:200],
                "venue": "unknown",
                "year": year,
                "status": "inferred",
                "pdfs": pdfs,
                "themes": [],
                "one": "Docked PDF — fill themes and abstract in builder/entries.",
                "flag": "Auto-mapped by SCUBA — edit builder/entries/{}/{}.md then re-surface.".format(channel_id, slug),
                "channel": channel_id,
            }
        else:
            entry = {
                "slug": slug,
                "entry": entry_rel,
                "title": title[:200],
                "source_file": rel_source,
                "source_type": cfg.get("source_type", "note"),
                "channel": channel_id,
                "status": "staged",
                "date_ingested": datetime.date.today().isoformat(),
                "one": "Docked artifact — fill entry note; LLM Deep Dive pending.",
                "flag": "Edit builder/entries/{}/{}.md — generative sections via Deep Dive later.".format(channel_id, slug),
            }
        new_entries.append(entry)
        print("  map: {} → {} ({})".format(fname, slug, entry_rel))

    if dry_run:
        return new_entries

    if profile == "portfolio":
        merged = channel_auto + new_entries
        _write_auto(builder_dir, merged, auto_file, auto_key, channel_id)
        if not dry_run:
            for e in merged:
                _write_deepdive(vault, channel_id, e["slug"], dry_run=False)
    else:
        merged_channel = channel_auto + new_entries
        _merge_auto_sources(builder_dir, channel_id, merged_channel, auto_file, auto_key)
        if not dry_run:
            for e in merged_channel:
                _write_deepdive(vault, channel_id, e["slug"], dry_run=False)

    return new_entries


def main():
    vault = os.path.dirname(BUILDER_DIR)
    dry_run = "--dry-run" in sys.argv
    channel_id = "my-portfolio"

    if "--vault" in sys.argv:
        vault = os.path.abspath(sys.argv[sys.argv.index("--vault") + 1])
    if "--channel" in sys.argv:
        channel_id = sys.argv[sys.argv.index("--channel") + 1]

    if subprocess.call(["which", "pdftotext"], stdout=subprocess.DEVNULL) != 0:
        print("warning: pdftotext not found — PDF titles will fall back to filenames")

    print("channel: {}".format(channel_id))
    mapped = map_channel(vault, channel_id, dry_run=dry_run)
    if mapped:
        print("mapped {} artifact(s) → builder/entries/{}".format(len(mapped), channel_id))
    else:
        cfg = CHANNELS[channel_id]
        print("no unmapped files in {}".format(cfg["raw_path"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
