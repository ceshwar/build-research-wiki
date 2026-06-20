"""Tests for builder/slug_util.py and theme deduplication."""
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "builder"))

from slug_util import canonical_slug, dedupe_themes, build_theme_resolver  # noqa: E402


def test_canonical_slug():
    assert canonical_slug("Digital-Governance") == "digital-governance"
    assert canonical_slug("Digital Governance") == "digital-governance"
    assert canonical_slug("  COMPUTATIONAL_SOCIAL_SCIENCE ") == "computational-social-science"


def test_dedupe_themes_by_case():
    themes = {
        "digital-governance": ("Digital Governance", "core a", True),
        "Digital-Governance": ("digital governance", "core b", False),
    }
    merged, aliases = dedupe_themes(themes)
    assert list(merged.keys()) == ["digital-governance"]
    assert merged["digital-governance"][0] == "Digital Governance"
    assert aliases["Digital-Governance"] == "digital-governance"


def test_resolve_theme_slug_variants():
    themes = {
        "algorithmic-ai-audits": ("Algorithmic and AI Audits", "core", True),
        "mental-health-wellbeing": ("Mental Health and Well-being", "core", True),
    }
    resolve, merged, _ = build_theme_resolver(themes)
    assert resolve("algorithmic-and-ai-audits") == "algorithmic-ai-audits"
    assert resolve("mental-health-and-well-being") == "mental-health-wellbeing"
    assert len(merged) == 2
