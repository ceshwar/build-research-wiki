#!/usr/bin/env python3
"""QA: Quick Dip must not guess — only PDF-derived facts."""
import os
import sys
import tempfile
import shutil

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BUILDER_DIR)
sys.path.insert(0, BUILDER_DIR)

from quick_dip import extract_pdf, build_quick_dip_entry


FORBIDDEN = ("unknown", "theme-slug", "Auto-mapped", "Docked PDF", "fill themes", "Pending LLM",
             "abstracting with credit", "permissions@acm.org")


def test_extract_real_pdf():
    pdf = os.path.join(REPO, "examples/minimal-vault/raw/papers/chi2025-positive-reinforcement.pdf")
    if not os.path.exists(pdf):
        print("SKIP: demo PDF missing")
        return True
    r = extract_pdf(pdf)
    assert r["title"], "title should be extracted from PDF"
    assert r["abstract"], "abstract should be extracted from PDF"
    assert r["venue"] == "CHI", "venue should be CHI from PDF"
    assert r["year"] == 2025, "year should be 2025 from PDF/filename"
    assert "unknown" not in r["venue"].lower()
    print("  extract chi2025: title={!r:.60} venue={} year={} abstract_len={}".format(
        r["title"], r["venue"], r["year"], len(r["abstract"])))
    return True


def test_entry_no_placeholders():
    r = extract_pdf(os.path.join(REPO, "examples/minimal-vault/raw/papers/2502.20491v3.pdf"))
    body = build_quick_dip_entry(r)
    for bad in FORBIDDEN:
        assert bad.lower() not in body.lower(), "placeholder {!r} in entry".format(bad)
    assert "chart-tier: quick-dip" in body
    if r["abstract"]:
        assert r["abstract"][:40] in body
    print("  entry body: no placeholders, abstract embedded={}".format(bool(r["abstract"])))
    return True


def test_map_pipeline():
    import map_channel
    tmp = tempfile.mkdtemp(prefix="scuba-qa-")
    try:
        shutil.copytree(os.path.join(REPO, "builder"), os.path.join(tmp, "builder"))
        for d in ["raw/papers", "wiki/papers", "builder/entries/my-portfolio"]:
            os.makedirs(os.path.join(tmp, d), exist_ok=True)
        src = os.path.join(REPO, "examples/minimal-vault/raw/papers/chi2026-language-of-approval-2.pdf")
        shutil.copy(src, os.path.join(tmp, "raw/papers/lang-approval-qa.pdf"))
        # minimal data.py
        with open(os.path.join(tmp, "builder/data.py"), "w") as f:
            f.write("THEMES={}\nP=[]\nTITLES={}\nCONCEPTS={}\nPEOPLE={}\nPLATFORMS={}\nMETHODS={}\n")
        mapped = map_channel.map_channel(tmp, "my-portfolio")
        assert len(mapped) == 1, "expected 1 mapped paper"
        e = mapped[0]
        assert e["status"] == "quick-dip"
        assert e["venue"] in ("CHI", ""), "venue must be factual or empty"
        assert e.get("year") in (2026, None), "year from PDF only"
        assert "unknown" not in e.get("venue", "")
        entry_path = os.path.join(tmp, e["entry"])
        assert os.path.exists(entry_path)
        text = open(entry_path).read()
        for bad in FORBIDDEN:
            assert bad.lower() not in text.lower()
        dd = os.path.join(tmp, "builder/deepdives", e["slug"] + ".md")
        assert not os.path.exists(dd), "quick dip must not create deepdives/"
        print("  map_channel: status={} venue={} year={} no deepdive scaffold".format(
            e["status"], e.get("venue"), e.get("year")))
        return True
    finally:
        shutil.rmtree(tmp)


def test_no_false_abstract():
    pdf = os.path.join(REPO, "examples/minimal-vault/raw/papers/choi-convex.pdf")
    if not os.path.exists(pdf):
        return True
    r = extract_pdf(pdf)
    assert "abstracting with credit" not in r["abstract"].lower()
    assert "permission" not in r["abstract"][:80].lower()
    if r["abstract"]:
        assert "ConvEx" in r["abstract"] or "Discord" in r["abstract"]
    print("  choi-convex: no false abstract, len={}".format(len(r["abstract"])))
    return True


def main():
    ok = True
    for fn in (test_extract_real_pdf, test_entry_no_placeholders, test_no_false_abstract, test_map_pipeline):
        try:
            fn()
        except Exception as ex:
            print("FAIL {}: {}".format(fn.__name__, ex))
            ok = False
    print("quick_dip QA:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
