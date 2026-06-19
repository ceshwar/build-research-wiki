#!/usr/bin/env python3
"""Quick Dip (Tier 1) — extract only factual fields from artifacts. No guessing."""

import os
import re
import subprocess

# Venue tokens found on first pages — matched as whole words / phrases only.
VENUE_PATTERNS = [
    (r"\bCHI\s*['']?\s*(\d{4})\b", "CHI"),
    (r"\bCSCW\s*2\b", "CSCW"),
    (r"\bCSCW\s*['']?\s*(\d{4})\b", "CSCW"),
    (r"\bICWSM\s*['']?\s*(\d{4})\b", "ICWSM"),
    (r"\bNeurIPS\s*['']?\s*(\d{4})\b", "NeurIPS"),
    (r"\bACL\s*['']?\s*(\d{4})\b", "ACL"),
    (r"\bEMNLP\s*['']?\s*(\d{4})\b", "EMNLP"),
    (r"\bNAACL\s*['']?\s*(\d{4})\b", "NAACL"),
    (r"\bUIST\s*['']?\s*(\d{4})\b", "UIST"),
    (r"\bCSCW\b", "CSCW"),
    (r"\bCHI\b", "CHI"),
    (r"\bICWSM\b", "ICWSM"),
    (r"\barXiv:(\d{4})\.(\d{4,5})\b", "arXiv"),
    (r"\bProceedings of the ACM\b", "ACM"),
]

ABSTRACT_STOP = re.compile(
    r"(?i)^\s*(introduction|keywords|key\s*words|ccs\s*concepts|"
    r"1\s*introduction|index\s*terms|background|related\s*work|"
    r"ACM\s*Reference\s*Format|permission\s*to\s*make)\b"
)


def _pdftotext(pdf_path, first_page=1, last_page=3):
    try:
        out = subprocess.check_output(
            ["pdftotext", "-f", str(first_page), "-l", str(last_page), pdf_path, "-"],
            stderr=subprocess.DEVNULL,
        )
        return out.decode("utf-8", errors="replace")
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""


def _extract_title_page1(text):
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return ""
    title_parts = []
    for ln in lines[:8]:
        if re.search(r"(?i)^abstract\s*:?\s*$", ln):
            break
        if re.search(r"(?i)abstract|introduction|keywords|copyright|doi\.org|arxiv:", ln):
            break
        if re.match(r"^\d+$", ln):
            continue
        if len(ln) > 200:
            continue
        title_parts.append(ln)
        if len(" ".join(title_parts)) > 50:
            break
    return " ".join(title_parts).strip()[:300]


ABSTRACT_BAD_START = re.compile(
    r"(?i)^(abstracting|ing with|permission|copyright|to copy|all rights|doi\.org|https?://)"
)


def _extract_abstract(text):
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        stripped = ln.strip()
        if re.match(r"(?i)^\s*abstract\s*:?\s*$", stripped):
            start = i + 1
            break
        m = re.match(r"(?i)^\s*abstract\s*:\s*(.+)$", stripped)
        if m and m.group(1).strip():
            start = i
            lines[i] = m.group(1).strip()
            break
    if start is not None:
        body = _collect_abstract_lines(lines, start)
        if body and not ABSTRACT_BAD_START.match(body):
            return body
    return _extract_implicit_abstract(text)


def _collect_abstract_lines(lines, start):
    parts = []
    for ln in lines[start:]:
        s = ln.strip()
        if not s:
            if parts:
                parts.append("")
            continue
        if ABSTRACT_STOP.match(s):
            break
        parts.append(s)
    body = re.sub(r"\s+", " ", "\n".join(parts).strip())
    if len(body) < 40:
        return ""
    return body[:8000]


def _extract_implicit_abstract(text):
    """ACM-style papers often omit an Abstract heading — grab prose before CCS/Introduction."""
    lines = text.splitlines()
    stop_markers = re.compile(
        r"(?i)^(ccs\s*concepts|additional\s+key\s+words|keywords|key\s*words|"
        r"acm\s+reference\s+format|1\s+introduction|introduction|index\s*terms)\b"
    )
    collecting = False
    parts = []
    for i, ln in enumerate(lines[:80]):
        s = ln.strip()
        if not s:
            continue
        if stop_markers.match(s):
            break
        if re.search(r"(?i)doi\.org|copyright|permission|abstracting", s):
            break
        if not collecting:
            if i >= 3 and len(s) >= 80 and re.match(r'^[A-Z"“]', s):
                if not re.search(r"(?i)university|@|\.edu|department", s):
                    collecting = True
                    parts.append(s)
            continue
        if s.isupper() and len(s) < 40:
            break
        parts.append(s)
    body = re.sub(r"\s+", " ", " ".join(parts).strip())
    if len(body) < 120 or ABSTRACT_BAD_START.match(body):
        return ""
    if not _abstract_sane(body):
        return ""
    return body[:8000]


def _abstract_sane(body):
    """Reject fragmented grabs — empty is better than a wrong abstract."""
    if body.count("(") != body.count(")"):
        return False
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if len(s.strip()) > 20]
    if len(sentences) < 2:
        return False
    return True


def _extract_venue_year(text, filename=""):
    venue = ""
    year = None
    blob = text[:12000]
    for pattern, vname in VENUE_PATTERNS:
        m = re.search(pattern, blob)
        if m:
            venue = vname
            if m.lastindex and m.group(1) and re.match(r"^\d{4}$", m.group(1)):
                year = int(m.group(1))
            break
    if year is None and filename:
        m = re.search(r"(20\d{2}|19\d{2})", filename)
        if m:
            year = int(m.group(1))
    if year is None:
        ym = re.search(r"(?i)\b(20\d{2}|19\d{2})\b", blob[:3000])
        if ym:
            year = int(ym.group(1))
    return venue, year


def extract_pdf(pdf_path):
    """Return factual fields from PDF. Missing fields are empty/None — never guessed."""
    text = _pdftotext(pdf_path, 1, 4)
    fname = os.path.basename(pdf_path)
    title = _extract_title_page1(text)
    title_from = "pdf" if title else ""
    if not title:
        title = ""  # no filename fallback — Deep Dive or user fills
    abstract = _extract_abstract(text)
    venue, year = _extract_venue_year(text, fname)
    return {
        "title": title,
        "abstract": abstract,
        "venue": venue,
        "year": year,
        "title_from": title_from,
        "has_pdf_text": bool(text.strip()),
    }


def extract_text_file(path):
    """Factual title from first markdown H1 or first non-empty line."""
    try:
        with open(path) as f:
            for ln in f:
                s = ln.strip()
                if s.startswith("#"):
                    return {"title": s.lstrip("#").strip()[:300], "abstract": "", "venue": "", "year": None}
                if s and not s.startswith("<!--"):
                    return {"title": s[:300], "abstract": "", "venue": "", "year": None}
    except OSError:
        pass
    return {"title": "", "abstract": "", "venue": "", "year": None}


def build_quick_dip_entry(extracted):
    """Minimal chart entry — PDF facts only, empty sections otherwise."""
    lines = ["<!-- chart-tier: quick-dip — PDF-derived fields only; Deep Dive to enrich -->", ""]
    if extracted.get("abstract"):
        lines += ["## Abstract", "", extracted["abstract"], ""]
    else:
        lines += ["## Abstract", ""]
    lines += ["## One-liner", "", "## My notes", ""]
    return "\n".join(lines)


def format_venue_year(venue, year):
    v = venue or "—"
    y = str(year) if year else "—"
    return v, y
