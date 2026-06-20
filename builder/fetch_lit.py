#!/usr/bin/env python3
"""Expand the field layer from what the portfolio cites (OpenAlex → builder/lit/store.json).

Pipeline (LIT-EXPANSION-SPEC §4): resolve each portfolio paper to an OpenAlex work by
**DOI/arXiv ID (never fuzzy title)**, read its `referenced_works`, batch-fetch metadata,
dedupe by canonical OpenAlex ID, accumulate `seed_from`, and write store records that
`engine_lit.py` renders. PDF-bibliography parsing is the **fallback** (when OpenAlex returns
0 references), never the primary path — it is left as a hook here.

    python3 builder/fetch_lit.py --vault . --theme digital-governance --mailto you@example.edu

The HTTP layer is injectable (`OpenAlexClient(fetch=...)`) so the transforms are unit-tested
without the network. Stdlib only (urllib/json) — no new deps, Python 3.7+.
"""
import datetime
import importlib.util
import json
import os
import re
import sys
import urllib.parse
import urllib.request

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))
STOPWORDS = {"the", "a", "an", "of", "on", "in", "for", "and", "to", "with", "from", "by", "at", "is"}


# ---------- pure transforms (no network) ----------

def short_id(url_or_id):
    return (url_or_id or "").rsplit("/", 1)[-1]


def invert_abstract(inv):
    """OpenAlex returns an inverted index; reconstruct plain text."""
    if not inv:
        return ""
    positions = []
    for word, idxs in inv.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(w for _, w in positions)


def venue_of(work):
    loc = work.get("primary_location") or {}
    src = loc.get("source") or {}
    name = src.get("display_name")
    if name:
        return name
    for loc in work.get("locations", []) or []:
        src = (loc or {}).get("source") or {}
        if src.get("display_name"):
            return src["display_name"]
    return ""


def slugify(authors, year, title):
    last = ""
    if authors:
        parts = re.sub(r"[^A-Za-z\s'-]", "", authors[0]).split()
        last = parts[-1] if parts else authors[0]
    kw = [w for w in re.sub(r"[^a-z0-9\s]", " ", (title or "").lower()).split()
          if w not in STOPWORDS][:2]
    base = "-".join([p for p in [last.lower()] + [str(year or "")] + kw if p])
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "", base)).strip("-") or "work"


def work_to_record(work, seed_from, today=None):
    """Map an OpenAlex work JSON to a store.json record (LIT-EXPANSION-SPEC §1)."""
    today = today or datetime.date.today().isoformat()
    doi = (work.get("doi") or "").replace("https://doi.org/", "")
    ids = {"openalex": short_id(work.get("id", ""))}
    if doi:
        ids["doi"] = doi
        m = re.match(r"(?i)10\.48550/arxiv\.(.+)", doi)
        if m:
            ids["arxiv"] = m.group(1)
    authors = [a["author"]["display_name"] for a in work.get("authorships", [])
               if a.get("author") and a["author"].get("display_name")]
    oa = work.get("best_oa_location") or work.get("primary_location") or {}
    url = oa.get("pdf_url") or oa.get("landing_page_url") or (("https://doi.org/" + doi) if doi else "")
    title = work.get("title") or work.get("display_name") or ""
    year = work.get("publication_year")
    return {
        "slug": slugify(authors, year, title),
        "ids": ids,
        "title": title,
        "authors": authors,
        "venue": venue_of(work),
        "year": year,
        "url": url,
        "abstract": invert_abstract(work.get("abstract_inverted_index")),
        "cited_by_count": work.get("cited_by_count", 0) or 0,
        "depth": "stub",
        "seed_from": sorted(seed_from),
        "discovered_via": "portfolio-citation",
        "themes": [], "concepts": [], "one_liner": "", "relates": "",
        "cites": [], "cited_by": [],
        "added": today,
        "note": "",
    }


def _dedupe_slugs(records):
    """Stable slug collisions → append -b, -c (canonical identity stays in ids.openalex)."""
    seen = {}
    for r in records:
        base = r["slug"]
        if base not in seen:
            seen[base] = 1
            continue
        seen[base] += 1
        r["slug"] = "{}-{}".format(base, chr(ord("a") + seen[base] - 1))
    return records


SORT_KEYS = ("year", "seed_count", "cited_by_count")


def _sort_value(r, sort_by):
    if sort_by == "seed_count":
        return len(r.get("seed_from", []))
    if sort_by == "cited_by_count":
        return r.get("cited_by_count") or 0
    return r.get("year") or 0          # 'year' default; missing year → 0 (sorts last, desc)


def rank(records, sort_by="year"):
    """§1.1: primary key desc by sort_by; tie-break cited_by_count desc, then seed_count desc."""
    records.sort(key=lambda r: (-_sort_value(r, sort_by),
                                -(r.get("cited_by_count") or 0),
                                -len(r.get("seed_from", []))))
    return records


# ---------- OpenAlex client (injectable network) ----------

class OpenAlexClient:
    BASE = "https://api.openalex.org"

    def __init__(self, mailto, fetch=None):
        self.mailto = mailto
        self._fetch = fetch or self._http

    def _http(self, url):
        req = urllib.request.Request(
            url, headers={"User-Agent": "build-research-wiki/0.1 (mailto:{})".format(self.mailto)})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))

    def _get(self, path, params=None):
        params = dict(params or {})
        params["mailto"] = self.mailto
        return self._fetch("{}/{}?{}".format(self.BASE, path, urllib.parse.urlencode(params)))

    def work_by_doi(self, doi):
        try:
            return self._get("works/doi:{}".format(doi))
        except Exception:
            return None

    def work_by_id(self, oaid):
        try:
            return self._get("works/{}".format(oaid))
        except Exception:
            return None

    def works_batch(self, ids, chunk=50):
        out = []
        for i in range(0, len(ids), chunk):
            sub = ids[i:i + chunk]
            page = self._get("works", {"filter": "openalex_id:" + "|".join(sub), "per-page": 200})
            out.extend(page.get("results", []))
        return out


# ---------- portfolio resolution + orchestration ----------

def resolve_portfolio_work(paper, client):
    """Resolve a portfolio paper dict to its OpenAlex work via DOI then arXiv ID. Never by title."""
    doi = paper.get("doi")
    if doi:
        w = client.work_by_doi(doi.replace("https://doi.org/", ""))
        if w:
            return w
    arxiv = paper.get("arxiv")
    if arxiv:
        w = client.work_by_doi("10.48550/arXiv.{}".format(arxiv))
        if w:
            return w
    return None


def _pdf_reference_fallback(vault, paper):
    """FALLBACK ONLY (OpenAlex returned 0 refs). Parse local PDF References via
    GROBID/anystyle/LLM — NOT regex (LIT-EXPANSION-SPEC §4). Not yet implemented; returns []
    so the caller records the paper as needing fallback rather than fabricating edges."""
    return []


def build_exclusion(papers, client):
    """Amendment 4: a portfolio paper's references include OTHER portfolio papers (we cite
    ourselves) — drop those from the field layer. Returns (openalex_ids, dois, resolved_works)."""
    ids, dois, resolved = set(), set(), {}
    for p in papers:
        if p.get("doi"):
            dois.add(p["doi"].replace("https://doi.org/", "").lower())
        work = resolve_portfolio_work(p, client)
        if work:
            resolved[p["slug"]] = work
            ids.add(short_id(work.get("id", "")))
            d = (work.get("doi") or "").replace("https://doi.org/", "").lower()
            if d:
                dois.add(d)
    return ids, dois, resolved


def expand_from_portfolio(vault, seed_papers, client, all_papers=None,
                          sort_by="year", limit=10, today=None, write=True):
    """Harvest what the seed papers cite → ranked, capped field-layer stub records.

    `all_papers` (default = seed_papers) builds the Amendment-4 exclusion set; pass the FULL
    portfolio so a seed citing a non-seed portfolio paper is still excluded.
    """
    today = today or datetime.date.today().isoformat()
    all_papers = all_papers if all_papers is not None else seed_papers
    excl_ids, excl_dois, resolved = build_exclusion(all_papers, client)

    seed_map = {}            # openalex id -> {"work": json, "seed_from": set()}
    needs_fallback, unresolved, excluded = [], [], 0
    for p in seed_papers:
        work = resolved.get(p["slug"]) or resolve_portfolio_work(p, client)
        if not work:
            unresolved.append(p["slug"])
            continue
        ref_ids = [short_id(u) for u in work.get("referenced_works", []) if u]
        if not ref_ids:
            if not _pdf_reference_fallback(vault, p):
                needs_fallback.append(p["slug"])
            continue
        for rw in client.works_batch(ref_ids):
            oaid = short_id(rw.get("id", ""))
            if not oaid:
                continue
            rdoi = (rw.get("doi") or "").replace("https://doi.org/", "").lower()
            if oaid in excl_ids or (rdoi and rdoi in excl_dois):
                excluded += 1                       # Amendment 4: self-cited portfolio paper
                continue
            slot = seed_map.setdefault(oaid, {"work": rw, "seed_from": set()})
            slot["seed_from"].add(p["slug"])

    candidates = rank([work_to_record(s["work"], s["seed_from"], today)
                       for s in seed_map.values()], sort_by)
    total = len(candidates)
    selected = candidates if limit in (None, "all") else candidates[:int(limit)]
    selected = _dedupe_slugs(selected)
    for i, r in enumerate(selected, 1):
        r["selection"] = {"sort_by": sort_by, "limit": limit, "rank": i, "candidates_total": total}

    dropped = write_store(vault, selected) if write else 0
    return {"records": selected, "candidates_total": total, "excluded": excluded,
            "dropped_stubs": dropped, "needs_fallback": needs_fallback, "unresolved": unresolved}


def _merge(existing, new_records):
    """§1.1 merge-on-rerun: preserve manual-upload + mapped/deepdive records (agent enrichment);
    replace portfolio-citation stubs with the new top-N; drop stale stubs not reselected."""
    def oaid(r):
        return (r.get("ids") or {}).get("openalex", "")

    preserved, preserved_ids = [], set()
    for r in existing:
        if r.get("discovered_via") == "manual-upload" or r.get("depth", "stub") in ("mapped", "deepdive"):
            preserved.append(r)
            preserved_ids.add(oaid(r))
    new_ids = {oaid(r) for r in new_records}
    dropped = sum(1 for r in existing
                  if r.get("discovered_via") == "portfolio-citation" and r.get("depth", "stub") == "stub"
                  and oaid(r) not in new_ids and oaid(r) not in preserved_ids)
    merged = preserved + [r for r in new_records if oaid(r) not in preserved_ids]
    return merged, dropped


def write_store(vault, new_records):
    """Merge with any existing store (preserving enrichment), write JSON, return #dropped stubs."""
    out = os.path.join(vault, "builder", "lit", "store.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    existing = []
    if os.path.exists(out):
        try:
            existing = json.load(open(out))
        except (ValueError, OSError):
            existing = []
    merged, dropped = _merge(existing if isinstance(existing, list) else [], new_records)
    with open(out, "w") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return dropped


def _load_portfolio_papers(vault, theme=None, slugs=None):
    """Read data.py P; select the thread (by explicit slugs or theme) and surface doi/arxiv ids."""
    data_path = os.path.join(vault, "builder", "data.py")
    spec = importlib.util.spec_from_file_location("data", data_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    slugset = set(slugs) if slugs else None
    papers = []
    for p in getattr(mod, "P", []):
        if slugset is not None and p["slug"] not in slugset:
            continue
        if theme and theme not in (p.get("themes") or []):
            continue
        arxiv = p.get("arxiv")
        if not arxiv:  # best-effort: an arXiv id baked into a pdf filename (2502.20491v3.pdf)
            for pdf in p.get("pdfs", []) or []:
                m = re.search(r"\b(\d{4}\.\d{4,5})\b", os.path.basename(pdf))
                if m:
                    arxiv = m.group(1)
                    break
        papers.append({"slug": p["slug"], "doi": p.get("doi"), "arxiv": arxiv, "pdfs": p.get("pdfs", [])})
    return papers


def load_config(vault):
    """Read builder/lit/config.yaml (hop1.sort_by/limit, mailto); defaults if absent / no PyYAML."""
    cfg = {"sort_by": "year", "limit": 10, "mailto": None}
    try:
        import yaml
    except ImportError:
        return cfg
    path = os.path.join(vault, "builder", "lit", "config.yaml")
    if os.path.exists(path):
        data = yaml.safe_load(open(path)) or {}
        hop1 = data.get("hop1", {}) or {}
        cfg["sort_by"] = hop1.get("sort_by", cfg["sort_by"])
        cfg["limit"] = hop1.get("limit", cfg["limit"])
        cfg["mailto"] = data.get("mailto", cfg["mailto"])
    return cfg


def write_default_config(vault, mailto=None):
    try:
        import yaml
    except ImportError:
        return
    path = os.path.join(vault, "builder", "lit", "config.yaml")
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump({"hop1": {"sort_by": "year", "limit": 10}, "mailto": mailto or "you@example.edu"},
                       f, default_flow_style=False, sort_keys=False)


def _arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    vault = os.path.dirname(BUILDER_DIR)
    if "--vault" in sys.argv:
        vault = os.path.abspath(_arg("--vault"))
    cfg = load_config(vault)
    theme = _arg("--theme")
    slugs = [s for s in (_arg("--papers", "") or "").split(",") if s] or None
    mailto = _arg("--mailto") or cfg["mailto"]
    if not mailto:
        sys.exit("--mailto <email> required (OpenAlex polite pool) — or set it in builder/lit/config.yaml.")
    sort_by = _arg("--sort-by") or cfg["sort_by"]
    if sort_by not in SORT_KEYS:
        sys.exit("--sort-by must be one of: {}".format(", ".join(SORT_KEYS)))
    limit_raw = _arg("--limit", cfg["limit"])
    limit = "all" if str(limit_raw) == "all" else int(limit_raw)
    dry = "--dry-run" in sys.argv

    seed_papers = _load_portfolio_papers(vault, theme=theme, slugs=slugs)
    if not seed_papers:
        sys.exit("No portfolio papers selected (theme={}, papers={}).".format(theme, slugs))
    all_papers = _load_portfolio_papers(vault)   # full portfolio → Amendment-4 exclusion set

    print("expanding {} seed paper(s) · sort_by={} limit={} …".format(len(seed_papers), sort_by, limit))
    res = expand_from_portfolio(vault, seed_papers, OpenAlexClient(mailto), all_papers=all_papers,
                                sort_by=sort_by, limit=limit, write=not dry)
    print("  candidates {} → selected {}  (excluded {} self-citations)".format(
        res["candidates_total"], len(res["records"]), res["excluded"]))
    if res["unresolved"]:
        print("  unresolved (no DOI/arXiv): {}".format(", ".join(res["unresolved"])))
    if res["needs_fallback"]:
        print("  0 refs — needs PDF fallback: {}".format(", ".join(res["needs_fallback"])))
    if not dry:
        write_default_config(vault, mailto)
        print("  dropped {} stale stub(s) · → builder/lit/store.json (run build.py to render)".format(
            res["dropped_stubs"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
