"""Tests for builder/registry.py — the JSON store for generated Quick Dip registries,
including transparent migration of legacy executable-Python registries.
"""
import json
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "builder"))

import registry  # noqa: E402


def test_json_name_normalizes_legacy_and_new():
    assert registry.json_name("auto_papers.py") == "auto_papers.json"
    assert registry.json_name("auto_papers.json") == "auto_papers.json"


def test_save_then_load_roundtrip(tmp_path):
    entries = [dict(slug="a", title="A", year=2025), dict(slug="b", title="B", year=None)]
    registry.save(str(tmp_path), "auto_papers.json", entries)
    assert registry.load(str(tmp_path), "auto_papers.json") == entries


def test_missing_registry_loads_as_empty(tmp_path):
    assert registry.load(str(tmp_path), "auto_sources.json") == []


def test_load_migrates_legacy_py_when_no_json(tmp_path):
    # An old-style executable registry with no JSON beside it.
    (tmp_path / "auto_papers.py").write_text('P_AUTO = [{"slug": "legacy", "title": "Old"}]\n')
    out = registry.load(str(tmp_path), "auto_papers.json")
    assert out == [{"slug": "legacy", "title": "Old"}]


def test_save_removes_shadowing_legacy_py(tmp_path):
    (tmp_path / "auto_papers.py").write_text("P_AUTO = []\n")
    registry.save(str(tmp_path), "auto_papers.json", [dict(slug="new")])
    assert not (tmp_path / "auto_papers.py").exists()
    assert (tmp_path / "auto_papers.json").exists()


def test_json_is_valid_and_human_readable(tmp_path):
    registry.save(str(tmp_path), "auto_papers.json", [dict(slug="a", title="é—accent")])
    text = (tmp_path / "auto_papers.json").read_text()
    assert json.loads(text)[0]["title"] == "é—accent"  # ensure_ascii=False keeps it readable
