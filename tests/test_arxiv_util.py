"""Tests for arXiv detection."""

import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from builder import arxiv_util


def test_arxiv_from_filename():
    assert arxiv_util.detect_arxiv_id("2502.20491v3.pdf") == "2502.20491"


def test_arxiv_from_text():
    assert arxiv_util.detect_arxiv_id("paper.pdf", "Submitted to arXiv:2401.12345") == "2401.12345"


def test_preprint_label():
    assert arxiv_util.is_arxiv_preprint("arXiv", "2502.20491")
