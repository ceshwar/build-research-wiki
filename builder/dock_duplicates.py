#!/usr/bin/env python3
"""Detect duplicate papers when docking new PDFs."""

import difflib
import os
import re
import tempfile

import arxiv_util
import ingest_prompt


def _normalize_title(title):
    return re.sub(r"\s+", " ", (title or "").lower().strip())


def _pdf_basename_set(item, raw_path="raw/papers"):
    names = set()
    for pdf in item.get("pdfs") or []:
        pdf = pdf.replace("\\", "/")
        names.add(os.path.basename(pdf))
        names.add(pdf)
    return names


def _entry_abstract(vault, item):
    rel = item.get("entry") or item.get("note") or ""
    if not rel:
        return ""
    path = rel if rel.startswith("/") else os.path.join(vault, rel.replace("\\", "/"))
    if not os.path.isfile(path):
        return ""
    try:
        with open(path) as f:
            text = f.read()
        m = re.search(r"(?is)##\s*abstract\s*\n+(.*?)(?:\n##|\Z)", text)
        if m:
            return m.group(1).strip()
    except OSError:
        pass
    return ""


def find_duplicate_matches(vault, channel_id, filename, extracted=None):
    """Return list of {slug, title, match_type, pdf_path} for charted papers."""
    extracted = extracted or {}
    vault = os.path.abspath(vault)
    fname = os.path.basename(filename)
    new_title = _normalize_title(extracted.get("title"))
    new_arxiv = arxiv_util.detect_arxiv_id(fname, extracted.get("_pdf_text", ""))
    matches = []
    seen_slugs = set()

    for item in ingest_prompt._full_corpus(vault):
        if item.get("channel") != channel_id:
            continue
        slug = item.get("slug")
        if not slug or slug in seen_slugs:
            continue
        title = item.get("title") or slug
        pdfs = _pdf_basename_set(item)
        pdf_path = ""
        if item.get("pdfs"):
            pdf_path = item["pdfs"][0].replace("\\", "/")

        if fname in pdfs:
            matches.append({
                "slug": slug,
                "title": title,
                "match_type": "filename",
                "pdf_path": pdf_path,
            })
            seen_slugs.add(slug)
            continue

        item_arxiv = item.get("arxiv_id") or ""
        if not item_arxiv and pdf_path:
            item_arxiv = arxiv_util.detect_arxiv_id(os.path.basename(pdf_path))
        if new_arxiv and item_arxiv and new_arxiv == item_arxiv:
            matches.append({
                "slug": slug,
                "title": title,
                "match_type": "arxiv",
                "pdf_path": pdf_path,
            })
            seen_slugs.add(slug)
            continue

        if new_title and len(new_title) >= 12:
            old = _normalize_title(title)
            if old and difflib.SequenceMatcher(None, new_title, old).ratio() >= 0.88:
                matches.append({
                    "slug": slug,
                    "title": title,
                    "match_type": "title",
                    "pdf_path": pdf_path,
                })
                seen_slugs.add(slug)

    return matches


def extract_for_duplicate_check(file_path):
    """Light PDF extract for duplicate detection."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        import quick_dip
        data = quick_dip.extract_pdf(file_path)
        text = ""
        try:
            text = quick_dip._pdftotext(file_path, 1, 2)
        except Exception:
            pass
        data["_pdf_text"] = text
        arxiv_id = arxiv_util.detect_arxiv_id(os.path.basename(file_path), text)
        if arxiv_id:
            data["arxiv_id"] = arxiv_id
            if not data.get("venue"):
                data["venue"] = "arXiv"
            data["preprint"] = True
        return data
    if ext in (".md", ".txt"):
        import quick_dip
        return quick_dip.extract_text_file(file_path)
    return {"title": "", "abstract": "", "venue": "", "year": None}


def merge_entry_fields(existing_abs, new_abs, fields):
    """fields: dict title/abstract/notes -> existing|new|concatenate"""
    out = {}
    for key in ("title", "abstract", "notes"):
        choice = (fields or {}).get(key, "existing")
        old = existing_abs.get(key) or ""
        new = new_abs.get(key) or ""
        if choice == "new":
            out[key] = new
        elif choice == "concatenate":
            parts = [p for p in (old.strip(), new.strip()) if p]
            out[key] = "\n\n---\n\n".join(parts)
        else:
            out[key] = old or new
    return out


def apply_merge_to_entry(vault, channel_id, target_slug, new_extracted, merge_fields, new_pdf_rel):
    """Update builder entry + registry row for merged paper."""
    import registry

    builder = os.path.join(vault, "builder")
    entries_dir = os.path.join(builder, "entries", channel_id)
    entry_path = os.path.join(entries_dir, target_slug + ".md")
    existing = {"title": "", "abstract": "", "notes": ""}
    if os.path.isfile(entry_path):
        with open(entry_path) as f:
            body = f.read()
        m = re.search(r"(?is)##\s*abstract\s*\n+(.*?)(?:\n##|\Z)", body)
        if m:
            existing["abstract"] = m.group(1).strip()
        m = re.search(r"(?is)##\s*my notes\s*\n+(.*?)(?:\n##|\Z)", body)
        if m:
            existing["notes"] = m.group(1).strip()
    for item in ingest_prompt._full_corpus(vault):
        if item.get("slug") == target_slug:
            existing["title"] = item.get("title") or ""
            break

    new_fields = {
        "title": new_extracted.get("title") or "",
        "abstract": new_extracted.get("abstract") or "",
        "notes": "",
    }
    merged = merge_entry_fields(existing, new_fields, merge_fields)

    import quick_dip
    lines = ["<!-- chart-tier: quick-dip -->", ""]
    if merged.get("abstract"):
        lines += ["## Abstract", "", merged["abstract"], ""]
    else:
        lines += ["## Abstract", ""]
    lines += ["## One-liner", "", "## My notes", ""]
    if merged.get("notes"):
        lines += [merged["notes"], ""]
    os.makedirs(entries_dir, exist_ok=True)
    with open(entry_path, "w") as f:
        f.write("\n".join(lines))

    json_name = "auto_papers.json"
    rows = registry.load(builder, json_name)
    for row in rows:
        if row.get("slug") == target_slug and row.get("channel", channel_id) == channel_id:
            if merge_fields.get("title") == "new" and merged.get("title"):
                row["title"] = merged["title"]
            if merge_fields.get("pdf") == "new" and new_pdf_rel:
                row["pdfs"] = [new_pdf_rel]
            if new_extracted.get("arxiv_id"):
                row["arxiv_id"] = new_extracted["arxiv_id"]
                row["preprint"] = True
                if merge_fields.get("venue", "existing") == "new":
                    row["venue"] = new_extracted.get("venue") or "arXiv"
            break
    registry.save(builder, json_name, rows)

    data_path = os.path.join(builder, "data.py")
    if os.path.isfile(data_path):
        import completion
        data = completion._load_module(data_path)
        for row in getattr(data, "P", []):
            if row.get("slug") == target_slug:
                if merge_fields.get("title") == "new" and merged.get("title"):
                    row["title"] = merged["title"]
                if merge_fields.get("pdf") == "new" and new_pdf_rel:
                    row["pdfs"] = [new_pdf_rel]
                break
