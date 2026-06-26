"""Tests for wiki query context selection."""

import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from builder import wiki_query

EXAMPLE_VAULT = os.path.join(REPO, "examples", "minimal-vault")


def test_pick_all_chart_papers_from_corpus():
  pages = wiki_query._all_chart_paper_pages(EXAMPLE_VAULT, scope="all")
  paper_pages = [p for p in pages if p.startswith("wiki/papers/")]
  assert len(paper_pages) >= 6
  assert "wiki/papers/language-of-approval.md" in paper_pages


def test_focus_paper_includes_full_wiki_page():
  picked = wiki_query._pick_context_pages(
      EXAMPLE_VAULT,
      "approval language",
      paper_slugs=["language-of-approval"],
  )
  assert picked == ["wiki/papers/language-of-approval.md"]


def test_focus_theme_includes_theme_hub_and_papers():
  picked = wiki_query._pick_context_pages(
      EXAMPLE_VAULT,
      "algorithmic audit",
      theme_slugs=["algorithmic-ai-audits"],
  )
  assert "wiki/themes/algorithmic-ai-audits.md" in picked
  assert "wiki/papers/popular-feed-audit.md" in picked


def test_build_prompt_lists_sources_used():
  _prompt, sources = wiki_query.build_query_prompt(
      EXAMPLE_VAULT,
      "What drives positive feedback?",
      paper_slugs=["language-of-approval"],
  )
  assert "language-of-approval" in sources
  assert "[[language-of-approval]]" in _prompt
  assert "chart pages" in _prompt.lower()


def test_scope_verified_filters_papers():
  all_pages = wiki_query._all_chart_paper_pages(EXAMPLE_VAULT, scope="all")
  verified_pages = wiki_query._all_chart_paper_pages(EXAMPLE_VAULT, scope="verified")
  assert len(verified_pages) < len(all_pages)
  slugs = {
      os.path.splitext(os.path.basename(p))[0]
      for p in verified_pages
      if p.startswith("wiki/papers/")
  }
  assert "language-of-approval" in slugs
  uncharted = wiki_query._all_chart_paper_pages(EXAMPLE_VAULT, scope="uncharted")
  uncharted_slugs = {
      os.path.splitext(os.path.basename(p))[0] for p in uncharted if p.startswith("wiki/papers/")
  }
  assert "creator-hearts" in uncharted_slugs
  assert "language-of-approval" not in uncharted_slugs
