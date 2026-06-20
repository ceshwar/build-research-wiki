"""Tests for the completion state machine — the Dive Computer's source of truth.

States: pending → quick_dip → needs_deep_dive → processed. These classifications
drive the headline counts in the UI, so a misclassification is a visible product bug.
"""
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
EXAMPLE_VAULT = os.path.join(REPO_ROOT, "examples", "minimal-vault")
sys.path.insert(0, os.path.join(REPO_ROOT, "builder"))

import completion  # noqa: E402

CHARTED_ENTRY = "builder/entries/my-portfolio/language-of-approval.md"


# ---- end-to-end on the demo vault ---------------------------------------

def test_demo_vault_counts():
    rep = completion.assess_vault(EXAMPLE_VAULT, {})
    totals = rep["totals"]
    assert totals["on_chart"] == 6
    assert totals["processed"] == 3
    assert totals["quick_dip"] == 3
    for key in ("needs_deep_dive", "scaffolded", "pending"):
        assert totals[key] == 0, "expected 0 {}, got {}".format(key, totals[key])


def test_demo_entries_mix_processed_and_quick_dip():
    rep = completion.assess_vault(EXAMPLE_VAULT, {})
    statuses = {e["slug"]: e["status"] for e in rep["entries"]}
    assert statuses["positive-reinforcement-reddit"] == "processed"
    assert statuses["language-of-approval"] == "processed"
    assert statuses["popular-feed-audit"] == "processed"
    assert statuses["creator-hearts"] == "quick_dip"
    assert sum(1 for e in rep["entries"] if e["status"] == "quick_dip") == 3


# ---- assess_entry state transitions -------------------------------------

def _entry(**kw):
    base = dict(slug="x", entry=CHARTED_ENTRY, channel="my-portfolio",
                profile="portfolio", status="mapped", themes=["x"], one="")
    base.update(kw)
    return base


def test_charted_entry_without_deepdive_needs_deep_dive():
    # Real charted entry file, but a slug with no deepdive → not processed.
    a = completion.assess_entry(EXAMPLE_VAULT, _entry(slug="no-such-deepdive", status="quick-dip"))
    assert a["status"] == "needs_deep_dive"
    assert a["has_deepdive"] is False


def test_charted_entry_with_deepdive_is_processed():
    a = completion.assess_entry(EXAMPLE_VAULT, _entry(slug="language-of-approval"))
    assert a["status"] == "processed"


def test_bare_quick_dip_entry_is_quick_dip(tmp_path):
    # An entry file with only a (short) abstract — no themes, no one-liner.
    entry_dir = tmp_path / "builder" / "entries" / "my-portfolio"
    entry_dir.mkdir(parents=True)
    (entry_dir / "fresh.md").write_text(
        "<!-- chart-tier: quick-dip -->\n\n## Abstract\n\n## One-liner\n\n## My notes\n"
    )
    a = completion.assess_entry(
        str(tmp_path),
        dict(slug="fresh", entry="builder/entries/my-portfolio/fresh.md",
             channel="my-portfolio", profile="portfolio", status="quick-dip",
             themes=[], one=""),
    )
    assert a["status"] == "quick_dip"


# ---- classifier helpers --------------------------------------------------

def test_is_placeholder_flags_template_markers():
    assert completion._is_placeholder("theme-slug-one")
    assert completion._is_placeholder("")
    assert not completion._is_placeholder(
        "A genuine multi-sentence abstract that is clearly real research prose."
    )


def test_one_liner_completeness():
    assert not completion._one_complete("Auto-mapped from PDF", "")
    assert not completion._one_complete("", "")
    assert completion._one_complete(
        "", "Quasi-experiment on 11M posts identifies linguistic drivers of approval."
    )


def test_themes_completeness():
    assert not completion._themes_complete([], [])
    assert completion._themes_complete(["digital-governance"], [])
    assert completion._themes_complete([], ["parsed-theme"])
