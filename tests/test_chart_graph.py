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


def test_theme_labels_unique_case_insensitive(tmp_path):
    """Duplicate theme slugs differing only by case collapse to one graph node."""
    import shutil

    vault = tmp_path / "vault"
    shutil.copytree(EXAMPLE_VAULT, vault)
    data_path = vault / "builder" / "data.py"
    text = data_path.read_text()
    insert = '    "Digital-Governance": ("digital governance", "dup", False),\n'
    text = text.replace('    "digital-governance": (', insert + '    "digital-governance": (', 1)
    data_path.write_text(text)

    g = chart_graph.build_graph(str(vault), "my-portfolio")
    theme_nodes = [n for n in g["nodes"] if n["type"] == "theme"]
    labels_lower = [n["label"].lower() for n in theme_nodes]
    assert len(labels_lower) == len(set(labels_lower))
    slugs = {n["slug"] for n in theme_nodes}
    assert "digital-governance" in slugs
    assert "Digital-Governance" not in slugs


def test_local_reef_no_duplicate_theme_labels():
    local = os.path.join(REPO_ROOT, "examples", "local-reef")
    if not os.path.isdir(local):
        return
    g = chart_graph.build_graph(local, "my-portfolio")
    theme_nodes = [n for n in g["nodes"] if n["type"] == "theme"]
    labels_lower = [n["label"].lower() for n in theme_nodes]
    assert len(labels_lower) == len(set(labels_lower)), sorted(labels_lower)
