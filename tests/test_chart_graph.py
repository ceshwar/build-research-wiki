"""Tests for builder/chart_graph.py."""
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
EXAMPLE_VAULT = os.path.join(REPO_ROOT, "examples", "minimal-vault")
sys.path.insert(0, os.path.join(REPO_ROOT, "builder"))

import chart_graph  # noqa: E402


def test_demo_portfolio_graph():
    g = chart_graph.build_graph(EXAMPLE_VAULT, "my-portfolio")
    assert g["channel_id"] == "my-portfolio"
    assert len(g["nodes"]) >= 6
    types = {n["type"] for n in g["nodes"]}
    assert "paper" in types
    assert "theme" in types
    assert "concept" in types
    slugs = {n["slug"] for n in g["nodes"]}
    assert "positive-reinforcement-reddit" in slugs
    assert "healthy-online-behavior" in slugs
    assert "distributed-moderation" in slugs
    assert len(g["edges"]) >= 6
    kinds = {e["kind"] for e in g["edges"]}
    assert "link" in kinds
    assert "theme" in kinds


def test_non_portfolio_returns_empty():
    g = chart_graph.build_graph(EXAMPLE_VAULT, "lit-review")
    assert g["nodes"] == []
    assert g["edges"] == []
