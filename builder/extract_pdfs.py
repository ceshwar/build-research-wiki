#!/usr/bin/env python3
"""Helper: (re)build builder/cache/<slug>.txt by running pdftotext over each paper's PDF,
using the slug→PDF mapping in data.P. Run this when you add papers or need the raw text
for writing deep dives. Requires poppler:  brew install poppler

    python3 builder/extract_pdfs.py
"""
import os, sys, subprocess, importlib.util

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(BUILDER_DIR)


def load_data():
    spec = importlib.util.spec_from_file_location("data", os.path.join(BUILDER_DIR, "data.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def main():
    if subprocess.call(["which", "pdftotext"], stdout=subprocess.DEVNULL) != 0:
        sys.exit("pdftotext not found — install poppler (brew install poppler).")
    data = load_data()
    papers_dir = os.path.join(VAULT, "raw/papers")
    cache = os.path.join(BUILDER_DIR, "cache"); os.makedirs(cache, exist_ok=True)
    done = miss = 0
    for p in data.P:
        if not p["pdfs"]:
            continue
        pdf = os.path.join(papers_dir, p["pdfs"][0])
        if not os.path.exists(pdf):
            print(f"  ! missing PDF: {p['pdfs'][0]} ({p['slug']})"); miss += 1; continue
        subprocess.call(["pdftotext", pdf, os.path.join(cache, p["slug"] + ".txt")])
        done += 1
    print(f"extracted {done} → builder/cache/ ({miss} missing PDFs)")


if __name__ == "__main__":
    main()
