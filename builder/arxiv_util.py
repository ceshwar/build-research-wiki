#!/usr/bin/env python3
"""arXiv id detection from filenames and PDF text."""

import re

ARXIV_FILENAME = re.compile(r"^(\d{4}\.\d{4,5})(v\d+)?\.pdf$", re.IGNORECASE)
ARXIV_TEXT = re.compile(r"\barxiv:(\d{4}\.\d{4,5})(v\d+)?\b", re.IGNORECASE)


def detect_arxiv_id(filename="", text=""):
    """Return normalized arXiv id (e.g. 2502.20491) or empty string."""
    fn = (filename or "").strip()
    m = ARXIV_FILENAME.match(fn)
    if m:
        return m.group(1)
    blob = (text or "")[:15000]
    m = ARXIV_TEXT.search(blob)
    if m:
        return m.group(1)
    return ""


def is_arxiv_preprint(venue, arxiv_id=""):
    if arxiv_id:
        return True
    v = (venue or "").strip().lower()
    return v == "arxiv" or v.startswith("arxiv ")
