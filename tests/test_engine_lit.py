"""Tests for the external-literature engine (builder/engine_lit.py).

Validates the field layer against a synthetic store that references the demo vault's REAL
theme/concept/paper slugs, so the shared red-link check must stay green.
"""
import json
import os
import shutil
import subprocess
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
EXAMPLE_VAULT = os.path.join(REPO_ROOT, "examples", "minimal-vault")
sys.path.insert(0, os.path.join(REPO_ROOT, "builder"))

import engine_lit  # noqa: E402

# Synthetic golden slice — real demo slugs for seed_from / themes / concepts; illustrative metadata.
STORE = [
    {
        "slug": "grimmelmann-2015-virtues-of-moderation",
        "ids": {"openalex": "W0000000001", "doi": "10.0000/illus.1"},
        "title": "The Virtues of Moderation", "authors": ["Grimmelmann J."],
        "venue": "Yale JL & Tech", "year": 2015, "url": "https://example.org/g",
        "abstract": "Illustrative fixture abstract: a taxonomy of online community moderation.",
        "cited_by_count": 900, "depth": "stub",
        "seed_from": ["positive-reinforcement-reddit"], "discovered_via": "portfolio-citation",
        "themes": [], "concepts": [], "cites": [], "cited_by": [],
        "added": "2026-06-19", "note": "illustrative fixture record",
    },
    {
        "slug": "gillespie-2018-custodians-of-the-internet",
        "ids": {"openalex": "W0000000002", "doi": "10.0000/illus.2"},
        "title": "Custodians of the Internet", "authors": ["Gillespie T."],
        "venue": "Yale University Press", "year": 2018, "url": "https://example.org/c",
        "abstract": "Illustrative fixture abstract: platform content moderation at scale.",
        "cited_by_count": 1500, "depth": "mapped",
        "seed_from": ["positive-reinforcement-reddit", "popular-feed-audit"],
        "discovered_via": "portfolio-citation",
        "themes": ["digital-governance", "social-media-online-communities"],
        "concepts": ["distributed-moderation"],
        "one_liner": "Moderation is constitutive of platforms, not incidental to them.",
        "relates": "Governance backdrop for [[positive-reinforcement-reddit]].",
        "cites": ["grimmelmann-2015-virtues-of-moderation"], "cited_by": [],
        "added": "2026-06-19", "note": "illustrative fixture record",
    },
]


def _vault_with_store(tmp_path):
    dest = os.path.join(str(tmp_path), "vault")
    shutil.copytree(EXAMPLE_VAULT, dest)
    lit_dir = os.path.join(dest, "builder", "lit")
    os.makedirs(lit_dir)
    with open(os.path.join(lit_dir, "store.json"), "w") as f:
        json.dump(STORE, f)
    return dest


def test_full_build_stays_red_link_free(tmp_path):
    vault = _vault_with_store(tmp_path)
    r = subprocess.run([sys.executable, "builder/build.py", "--vault", vault],
                       cwd=REPO_ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "red links: NONE" in r.stdout
    assert "field lit 2" in r.stdout
    assert os.path.exists(os.path.join(vault, "wiki/lit/index.md"))
    assert os.path.exists(os.path.join(vault, "wiki/lit/gillespie-2018-custodians-of-the-internet.md"))


def test_pages_are_separated_field_corpus(tmp_path):
    vault = _vault_with_store(tmp_path)
    engine_lit.build(vault, "2026-06-19")
    page = open(os.path.join(vault, "wiki/lit/grimmelmann-2015-virtues-of-moderation.md")).read()
    assert "type: extpaper" in page
    assert "corpus: field" in page
    assert "[[positive-reinforcement-reddit]]" in page  # cited-by-your-work bridge


def test_cited_by_resolved_post_pass(tmp_path):
    vault = _vault_with_store(tmp_path)
    engine_lit.build(vault, "2026-06-19")
    grimmelmann = open(os.path.join(vault, "wiki/lit/grimmelmann-2015-virtues-of-moderation.md")).read()
    # Gillespie cites Grimmelmann → Grimmelmann's page gets the derived backward edge.
    assert "[[gillespie-2018-custodians-of-the-internet]]" in grimmelmann


def test_stub_vs_mapped_body(tmp_path):
    vault = _vault_with_store(tmp_path)
    engine_lit.build(vault, "2026-06-19")
    stub = open(os.path.join(vault, "wiki/lit/grimmelmann-2015-virtues-of-moderation.md")).read()
    mapped = open(os.path.join(vault, "wiki/lit/gillespie-2018-custodians-of-the-internet.md")).read()
    assert "## One-liner" not in stub and "[[digital-governance]]" not in stub
    assert "## One-liner" in mapped and "[[digital-governance]]" in mapped


def test_no_store_is_noop(tmp_path):
    # A vault without builder/lit/store.json must not create a lit layer.
    dest = os.path.join(str(tmp_path), "v2")
    shutil.copytree(EXAMPLE_VAULT, dest)
    assert engine_lit.build(dest, "2026-06-19") == {"lit": 0, "lit_built": 0}
    assert not os.path.exists(os.path.join(dest, "wiki/lit"))
