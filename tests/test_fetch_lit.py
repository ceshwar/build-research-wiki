"""Tests for builder/fetch_lit.py — OpenAlex transforms + orchestration, no network.

The HTTP client is faked; these pin the pure mappings and the seed_from/dedupe logic that
the golden acceptance slice will exercise for real.
"""
import json
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "builder"))

import fetch_lit  # noqa: E402


def _work(oaid, title, year=2018, author="Jane Smith", refs=None, cited=10, doi=None):
    w = {
        "id": "https://openalex.org/" + oaid, "title": title, "display_name": title,
        "publication_year": year,
        "authorships": [{"author": {"display_name": author}}],
        "cited_by_count": cited,
        "referenced_works": ["https://openalex.org/" + r for r in (refs or [])],
        "abstract_inverted_index": {"Online": [0], "moderation": [1], "matters": [2]},
    }
    if doi:
        w["doi"] = "https://doi.org/" + doi
    return w


class FakeClient:
    def __init__(self, by_doi, works):
        self.by_doi, self.works = by_doi, works

    def work_by_doi(self, doi):
        return self.by_doi.get(doi)

    def work_by_id(self, oaid):
        return None

    def works_batch(self, ids, chunk=50):
        return [self.works[i] for i in ids if i in self.works]


# ---------- pure transforms ----------

def test_invert_abstract():
    assert fetch_lit.invert_abstract({"a": [0], "b": [1, 3], "c": [2]}) == "a b c b"
    assert fetch_lit.invert_abstract(None) == ""


def test_slugify_skips_stopwords():
    assert fetch_lit.slugify(["James Grimmelmann"], 2015, "The Virtues of Moderation") == \
        "grimmelmann-2015-virtues-moderation"


def test_work_to_record_maps_fields_and_guards_nulls():
    w = _work("W42", "Custodians of the Internet", year=2018, author="Tarleton Gillespie",
              cited=1500, doi="10.5555/x")
    w["primary_location"] = {"source": None}  # null source must not crash
    r = fetch_lit.work_to_record(w, ["popular-feed-audit"], today="2026-06-19")
    assert r["ids"]["openalex"] == "W42"
    assert r["ids"]["doi"] == "10.5555/x"
    assert r["title"] == "Custodians of the Internet"
    assert r["authors"] == ["Tarleton Gillespie"]
    assert r["venue"] == ""                       # guarded null source
    assert r["abstract"] == "Online moderation matters"
    assert r["depth"] == "stub" and r["discovered_via"] == "portfolio-citation"
    assert r["seed_from"] == ["popular-feed-audit"]


def test_arxiv_doi_populates_arxiv_id():
    w = _work("W9", "A Preprint", doi="10.48550/arXiv.2502.20491")
    r = fetch_lit.work_to_record(w, ["x"])
    assert r["ids"]["arxiv"] == "2502.20491"


# ---------- orchestration: dedupe + seed_from accumulation ----------

def _fixture():
    p1 = _work("W1", "Portfolio One", refs=["W100", "W200"], doi="10.1/p1")
    p2 = _work("W2", "Portfolio Two", refs=["W200", "W300"], doi="10.1/p2")
    p4 = _work("W4", "No Refs", refs=[], doi="10.1/p4")
    by_doi = {"10.1/p1": p1, "10.1/p2": p2, "10.1/p4": p4}
    works = {"W100": _work("W100", "Cited Once A", author="Ann Lee"),
             "W200": _work("W200", "Cited By Both", author="Bob Ng", cited=99),
             "W300": _work("W300", "Cited Once B", author="Cara Poe")}
    return FakeClient(by_doi, works)


def test_seed_from_dedupes_and_accumulates(tmp_path):
    papers = [
        {"slug": "p1", "doi": "10.1/p1", "arxiv": None, "pdfs": []},
        {"slug": "p2", "doi": "10.1/p2", "arxiv": None, "pdfs": []},
        {"slug": "p3", "doi": None, "arxiv": None, "pdfs": []},   # unresolvable
    ]
    res = fetch_lit.expand_from_portfolio(str(tmp_path), papers, _fixture(), today="2026-06-19")
    by_slug = {r["slug"]: r for r in res["records"]}
    assert len(res["records"]) == 3                        # W100, W200, W300 (deduped)
    both = next(r for r in res["records"] if r["ids"]["openalex"] == "W200")
    assert both["seed_from"] == ["p1", "p2"]               # cited by both, accumulated
    assert res["records"][0]["ids"]["openalex"] == "W200"  # ranked first (2 seeds)
    assert res["unresolved"] == ["p3"]


def test_zero_refs_flags_pdf_fallback(tmp_path):
    papers = [{"slug": "p4", "doi": "10.1/p4", "arxiv": None, "pdfs": []}]
    res = fetch_lit.expand_from_portfolio(str(tmp_path), papers, _fixture(), today="2026-06-19")
    assert res["needs_fallback"] == ["p4"]
    assert res["records"] == []


def test_writes_valid_store_json(tmp_path):
    papers = [{"slug": "p1", "doi": "10.1/p1", "arxiv": None, "pdfs": []}]
    fetch_lit.expand_from_portfolio(str(tmp_path), papers, _fixture(), today="2026-06-19")
    store = os.path.join(str(tmp_path), "builder", "lit", "store.json")
    data = json.load(open(store))
    assert isinstance(data, list) and data[0]["discovered_via"] == "portfolio-citation"
