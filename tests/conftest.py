"""Shared test setup: put builder/ on the path and expose demo-vault locations.

Run from the repo root:  python3 -m pytest
"""
import os
import sys

import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
BUILDER_DIR = os.path.join(REPO_ROOT, "builder")
EXAMPLE_VAULT = os.path.join(REPO_ROOT, "examples", "minimal-vault")
PDF_DIR = os.path.join(EXAMPLE_VAULT, "raw", "papers")

# Builder modules (quick_dip, completion, …) import by bare name.
if BUILDER_DIR not in sys.path:
    sys.path.insert(0, BUILDER_DIR)

# The three demo PDFs and the venue/year they should resolve to.
DEMO_PDFS = {
    "chi2025-positive-reinforcement.pdf": ("CHI", 2025),
    "chi2026-language-of-approval-2.pdf": ("CHI", 2026),
    "2502.20491v3.pdf": (None, None),  # arXiv preprint — no conf token on page 1
}


@pytest.fixture
def example_vault():
    return EXAMPLE_VAULT


@pytest.fixture
def pdf_dir():
    return PDF_DIR
