"""Tests for the manual-agent ingest prompt generator (builder/ingest_prompt.py)."""
import json
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
EXAMPLE_VAULT = os.path.join(REPO_ROOT, "examples", "minimal-vault")
sys.path.insert(0, os.path.join(REPO_ROOT, "builder"))

import ingest_prompt  # noqa: E402

ABSTRACT = ("This paper studies how positive feedback shapes contributor behavior across many "
            "online communities, using a large-scale causal design and predictive modeling.")


def _quick_dip_vault(tmp_path):
    """Minimal vault with one Quick Dip portfolio entry that still needs enrichment."""
    builder = tmp_path / "builder"
    (builder / "entries" / "my-portfolio").mkdir(parents=True)
    (builder / "data.py").write_text("P = []\nS = []\n")
    (builder / "auto_papers.json").write_text(json.dumps([{
        "slug": "demo", "entry": "builder/entries/my-portfolio/demo.md",
        "note": "builder/entries/my-portfolio/demo.md", "title": "Demo Paper",
        "venue": "CHI", "year": 2025, "status": "quick-dip", "pdfs": ["demo.pdf"],
        "themes": [], "one": "", "channel": "my-portfolio",
    }]))
    (builder / "entries" / "my-portfolio" / "demo.md").write_text(
        "<!-- chart-tier: quick-dip -->\n\n## Abstract\n\n" + ABSTRACT + "\n\n## One-liner\n\n## My notes\n"
    )
    return str(tmp_path)


def test_nothing_to_do_on_fully_processed_demo():
    text, count = ingest_prompt.build_prompt(EXAMPLE_VAULT, "my-portfolio")
    assert count == 0
    assert "fully enriched" in text


def test_quick_dip_paper_is_listed_with_paths(tmp_path):
    vault = _quick_dip_vault(tmp_path)
    text, count = ingest_prompt.build_prompt(vault, "my-portfolio")
    assert count == 1
    assert "Demo Paper" in text
    assert "raw/papers/demo.pdf" in text          # source resolved from raw_path + filename
    assert "builder/deepdives/demo.md" in text     # deep dive target
    assert "CLAUDE.md" in text                      # grounded in the schema


def test_lists_only_actually_missing_pieces(tmp_path):
    vault = _quick_dip_vault(tmp_path)
    items = ingest_prompt.collect(vault, "my-portfolio")
    missing = " ".join(items[0]["missing"])
    assert "theme" in missing            # no theme links yet
    assert "One-liner" in missing        # no one-liner yet
    assert "deep dive" in missing        # no deepdive file
    assert "Abstract" not in missing     # Quick Dip already filled the abstract


def test_collect_skips_finished_pages():
    # Every demo entry is processed → nothing to collect.
    assert ingest_prompt.collect(EXAMPLE_VAULT, "my-portfolio") == []
