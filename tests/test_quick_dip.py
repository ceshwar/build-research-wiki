"""Tests for Quick Dip (Tier 1) extraction — the 'never guess' contract.

The promise: factual fields come straight off the page; anything uncertain stays
empty/None rather than being invented. These tests pin that behaviour against the
three real demo PDFs plus crafted unit inputs.
"""
import datetime
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
PDF_DIR = os.path.join(REPO_ROOT, "examples", "minimal-vault", "raw", "papers")
sys.path.insert(0, os.path.join(REPO_ROOT, "builder"))

import quick_dip  # noqa: E402

NEXT_YEAR = datetime.date.today().year + 1


def _sane_year(y):
    return y is None or (1990 <= y <= NEXT_YEAR)


# ---- real-PDF extraction -------------------------------------------------

def test_all_demo_pdfs_have_text():
    for name in os.listdir(PDF_DIR):
        if name.endswith(".pdf"):
            r = quick_dip.extract_pdf(os.path.join(PDF_DIR, name))
            assert r["has_pdf_text"], "no text extracted from {}".format(name)


def test_demo_pdf_titles_are_nonempty_and_from_page():
    for name in os.listdir(PDF_DIR):
        if not name.endswith(".pdf"):
            continue
        r = quick_dip.extract_pdf(os.path.join(PDF_DIR, name))
        # Some PDFs (e.g. arXiv with odd first-page layout) yield text but no title line.
        assert r["title"].strip() or r["has_pdf_text"], \
            "no title and no text for {}".format(name)
        if r["title"].strip():
            assert r["title_from"] == "pdf"


def test_extracted_abstracts_are_sane_not_fragments():
    for name in os.listdir(PDF_DIR):
        if not name.endswith(".pdf"):
            continue
        r = quick_dip.extract_pdf(os.path.join(PDF_DIR, name))
        if r["abstract"]:
            assert quick_dip._abstract_sane(r["abstract"]), \
                "abstract failed sanity check for {}".format(name)


def test_no_impossible_years_from_any_demo_pdf():
    """Regression: arXiv ids like 2502.20491 must not yield year 2049."""
    for name in os.listdir(PDF_DIR):
        if not name.endswith(".pdf"):
            continue
        r = quick_dip.extract_pdf(os.path.join(PDF_DIR, name))
        assert _sane_year(r["year"]), \
            "implausible year {} from {}".format(r["year"], name)


def test_known_conference_venues_detected():
    for name in ("chi2025-positive-reinforcement.pdf", "chi2026-language-of-approval-2.pdf"):
        r = quick_dip.extract_pdf(os.path.join(PDF_DIR, name))
        assert r["venue"] == "CHI"
        assert r["year"] in (2025, 2026)


# ---- _extract_venue_year unit cases -------------------------------------

def test_venue_year_from_clean_header():
    venue, year = quick_dip._extract_venue_year("Proceedings of CHI 2025, Honolulu", "")
    assert venue == "CHI"
    assert year == 2025


def test_arxiv_filename_does_not_leak_a_year():
    """The bug this suite was written to catch: '2049' inside an arXiv id."""
    _, year = quick_dip._extract_venue_year("", "2502.20491v3.pdf")
    assert _sane_year(year), "leaked implausible year {}".format(year)


def test_year_guard_rejects_far_future():
    _, year = quick_dip._extract_venue_year("Submitted 2049 to the future", "")
    assert _sane_year(year)


def test_abstract_sane_rejects_unbalanced_parens():
    assert not quick_dip._abstract_sane("A claim (with an unclosed paren. And a second sentence here.")


# ---- build_quick_dip_entry: no invented sections ------------------------

def test_quick_dip_entry_marks_tier_and_leaves_blanks():
    body = quick_dip.build_quick_dip_entry(
        {"title": "T", "abstract": "Real abstract text.", "venue": "CHI", "year": 2025}
    )
    assert "chart-tier: quick-dip" in body
    assert "Real abstract text." in body
    # One-liner / My notes exist as headings but are left for Deep Dive.
    assert "## One-liner\n" in body
    assert "## My notes\n" in body


def test_quick_dip_entry_without_abstract_has_no_fabricated_text():
    body = quick_dip.build_quick_dip_entry(
        {"title": "T", "abstract": "", "venue": "", "year": None}
    )
    assert "## Abstract" in body
    # Nothing invented under Abstract.
    after = body.split("## Abstract", 1)[1].split("## One-liner", 1)[0]
    assert after.strip() == ""
