"""map_channel._write_auto now persists registries as JSON via builder/registry.py.

These pin the property that mattered before (hostile titles round-trip exactly) and
that the output is data, not executable Python.
"""
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "builder"))

import map_channel  # noqa: E402
import registry  # noqa: E402


def _roundtrip(tmp_path, entries):
    map_channel._write_auto(str(tmp_path), entries, "auto_papers.json")
    return registry.load(str(tmp_path), "auto_papers.json")


def test_writes_json_not_python(tmp_path):
    map_channel._write_auto(str(tmp_path), [dict(slug="a", title="t")], "auto_papers.json")
    assert (tmp_path / "auto_papers.json").exists()
    assert not (tmp_path / "auto_papers.py").exists()


def test_hostile_title_roundtrips_exactly(tmp_path):
    entries = [dict(slug="x", title='He said "hi"\\bye', year=2025,
                    themes=["a"], one="", pdfs=["x.pdf"], channel="my-portfolio")]
    out = _roundtrip(tmp_path, entries)
    assert out[0]["title"] == 'He said "hi"\\bye'  # not 'hi' + backspace


def test_trailing_backslash_and_newline_survive(tmp_path):
    entries = [dict(slug="y", title="path\\\nnext line", year=2026, themes=[],
                    one="", pdfs=["y.pdf"], channel="my-portfolio")]
    out = _roundtrip(tmp_path, entries)
    assert out[0]["title"] == "path\\\nnext line"


def test_all_field_types_preserved(tmp_path):
    entries = [dict(slug="z", title="Plain", year=2025, themes=["a", "b"],
                    one="", pdfs=["z.pdf"], channel="my-portfolio")]
    out = _roundtrip(tmp_path, entries)
    assert out[0]["year"] == 2025
    assert out[0]["themes"] == ["a", "b"]
    assert out[0]["pdfs"] == ["z.pdf"]
