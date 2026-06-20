"""Tests for builder/chart_map.py."""
import json
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
EXAMPLE_VAULT = os.path.join(REPO_ROOT, "examples", "minimal-vault")
sys.path.insert(0, os.path.join(REPO_ROOT, "builder"))

import chart_map  # noqa: E402


def test_demo_portfolio_map():
    m = chart_map.build_map(EXAMPLE_VAULT, "my-portfolio")
    assert m["channel_id"] == "my-portfolio"
    assert m["raw_path"] == "raw/papers"
    assert m["wiki_folder"] == "wiki/papers"
    assert len(m["raw_files"]) == 7
    assert len(m["entries"]) == 7
    assert m["awaiting_chart"] == []
    slugs = {e["slug"] for e in m["entries"]}
    assert "creator-hearts" in slugs
    assert "positive-reinforcement-reddit" in slugs
    processed = [e for e in m["entries"] if e["status"] == "processed"]
    quick = [e for e in m["entries"] if e["status"] == "quick_dip"]
    assert len(processed) == 3
    assert len(quick) == 4
    assert len(m["themes"]) >= 5
    pr = next(e for e in m["entries"] if e["slug"] == "positive-reinforcement-reddit")
    assert len(pr["concepts"]) >= 2
    assert any(c["slug"] == "positive-reinforcement" for c in pr["concepts"])
    synth_slugs = {s["slug"] for s in pr["syntheses"]}
    assert "demo-reward-attention-thread" in synth_slugs


def test_ingest_prompt_lists_themes_and_full_pdf(tmp_path):
    import ingest_prompt
    builder = tmp_path / "builder"
    (builder / "entries" / "my-portfolio").mkdir(parents=True)
    (builder / "data.py").write_text(
        'THEMES = {"healthy-online-behavior": ("Healthy Online Behavior", "x", True)}\nP = []\nS = []\n'
    )
    (builder / "auto_papers.json").write_text(json.dumps([{
        "slug": "demo", "entry": "builder/entries/my-portfolio/demo.md",
        "title": "Demo", "year": 2025, "status": "quick-dip", "pdfs": ["demo.pdf"],
        "themes": [], "one": "", "channel": "my-portfolio",
    }]))
    (builder / "entries" / "my-portfolio" / "demo.md").write_text(
        "## Abstract\n\n" + "x" * 100 + "\n\n## One-liner\n"
    )
    text, count = ingest_prompt.build_prompt(str(tmp_path), "my-portfolio")
    assert count == 1
    assert "Read each source PDF in full" in text
    assert "[[healthy-online-behavior]]" in text
    assert "Allowed theme slugs" in text
