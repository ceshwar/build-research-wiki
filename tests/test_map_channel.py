"""Tests for the auto-registry codegen in map_channel._write_auto.

These registries are written as Python source and then `exec`'d on every dashboard
load, so a title with quotes/backslashes must round-trip exactly — never corrupt the
value or break the module import.
"""
import importlib.util
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "builder"))

import map_channel  # noqa: E402


def _roundtrip(tmp_path, entries):
    map_channel._write_auto(str(tmp_path), entries, "auto.py", "P_AUTO", "my-portfolio")
    path = os.path.join(str(tmp_path), "auto.py")
    spec = importlib.util.spec_from_file_location("auto", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.P_AUTO


def test_hostile_title_roundtrips_exactly(tmp_path):
    entries = [dict(slug="x", title='He said "hi"\\bye', year=2025,
                    themes=["a"], one="", pdfs=["x.pdf"], channel="my-portfolio")]
    out = _roundtrip(tmp_path, entries)
    assert out[0]["title"] == 'He said "hi"\\bye'  # not 'hi' + backspace


def test_trailing_backslash_does_not_break_import(tmp_path):
    entries = [dict(slug="y", title="path\\", year=2026, themes=[], one="",
                    pdfs=["y.pdf"], channel="my-portfolio")]
    out = _roundtrip(tmp_path, entries)  # would raise on a naive '"{}"' writer
    assert out[0]["title"] == "path\\"


def test_all_field_types_preserved(tmp_path):
    entries = [dict(slug="z", title="Plain", year=2025, themes=["a", "b"],
                    one="", pdfs=["z.pdf"], channel="my-portfolio")]
    out = _roundtrip(tmp_path, entries)
    assert out[0]["year"] == 2025
    assert out[0]["themes"] == ["a", "b"]
    assert out[0]["pdfs"] == ["z.pdf"]
