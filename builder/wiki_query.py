#!/usr/bin/env python3
"""Query the wiki — read chart pages (wiki markdown), answer with [[citations]]."""

import argparse
import json
import os
import re
import sys
import time

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))
if BUILDER_DIR not in sys.path:
    sys.path.insert(0, BUILDER_DIR)

import ingest_prompt
import llm_client
import llm_grounding


def _read(path, limit=8000):
    if not os.path.isfile(path):
        return ""
    with open(path) as f:
        text = f.read()
    return text[:limit]


def _paper_scope_index(vault):
    """slug -> verified, uncharted, needs_review for portfolio papers."""
    import completion

    out = {}
    for item in ingest_prompt._full_corpus(vault):
        assessed = completion.assess_entry(vault, item)
        slug = item.get("slug")
        if not slug:
            continue
        out[slug] = {
            "verified": bool(assessed.get("human_verified")),
            "llm_enriched": bool(assessed.get("llm_enriched")),
            "uncharted": not assessed.get("llm_enriched") and not assessed.get("human_verified"),
            "needs_review": bool(assessed.get("llm_enriched")) and not assessed.get("human_verified"),
        }
    return out


def _slug_in_scope(slug, scope, scope_index):
    if scope == "all" or not scope_index:
        return True
    info = scope_index.get(slug)
    if not info:
        return True
    if scope == "verified":
        return info["verified"]
    if scope == "uncharted":
        return info["uncharted"]
    if scope == "needs_review":
        return info["needs_review"]
    return True


def _page_in_scope(rel, scope, scope_index):
    if scope == "all" or not scope_index:
        return True
    for prefix in ("wiki/papers/", "wiki/sources/"):
        if rel.startswith(prefix) and rel.endswith(".md"):
            slug = os.path.splitext(os.path.basename(rel))[0]
            return _slug_in_scope(slug, scope, scope_index)
    return True


def _wiki_page_for_slug(vault, slug):
    for item in ingest_prompt._full_corpus(vault):
        if item.get("slug") == slug:
            profile = item.get("profile", "portfolio")
            if profile == "portfolio":
                return "wiki/papers/{}.md".format(slug)
            return "wiki/sources/{}.md".format(slug)
    return "wiki/papers/{}.md".format(slug)


def _papers_matching_themes(vault, theme_slugs):
    import chart_map

    theme_set = set(theme_slugs)
    slugs = []
    for item in ingest_prompt._full_corpus(vault):
        slug = item.get("slug")
        if not slug:
            continue
        for theme in chart_map._themes_for(item, vault):
            ts = theme["slug"] if isinstance(theme, dict) else theme
            if ts in theme_set:
                slugs.append(slug)
                break
    return slugs


def _all_chart_paper_pages(vault, scope="all"):
    scope_index = _paper_scope_index(vault) if scope != "all" else {}
    pages = []
    for sub in ("wiki/papers", "wiki/sources"):
        root = os.path.join(vault, sub)
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            if not name.endswith(".md"):
                continue
            rel = "{}/{}".format(sub, name)
            if _page_in_scope(rel, scope, scope_index):
                pages.append(rel)
    return pages


def _grep_relevant(vault, question, pages, top=8, scope="all"):
    scope_index = _paper_scope_index(vault) if scope != "all" else {}
    terms = [t.lower() for t in re.findall(r"[a-zA-Z]{4,}", question)]
    if not terms:
        return pages[:top]
    scored = []
    for rel in pages:
        if not _page_in_scope(rel, scope, scope_index):
            continue
        text = _read(os.path.join(vault, rel), limit=12000).lower()
        score = sum(text.count(t) for t in terms)
        if score > 0:
            scored.append((score, rel))
    scored.sort(reverse=True)
    return [rel for _s, rel in scored[:top]]


THIN_WIKI_CHARS = 900
PDF_EXCERPT_CHARS = 6000


def _corpus_item_for_slug(vault, slug):
    for item in ingest_prompt._full_corpus(vault):
        if item.get("slug") == slug:
            return item
    return None


def _pdf_path_for_item(vault, item):
    pdfs = item.get("pdfs") or []
    if not pdfs:
        return ""
    raw = pdfs[0].replace("\\", "/")
    if "/" in raw:
        return os.path.join(vault, raw)
    return os.path.join(vault, "raw", "papers", raw)


def _wiki_body_thin(body):
    if not body or len(body.strip()) < THIN_WIKI_CHARS:
        return True
    if "## Abstract / Notes" in body:
        chunk = body.split("## Abstract / Notes", 1)[-1]
        chunk = chunk.split("## Deep dive", 1)[0].strip()
        if len(chunk) < 80 or chunk.strip() in ("—", "-"):
            return True
    return False


def _pdf_excerpt_for_slug(vault, slug):
    item = _corpus_item_for_slug(vault, slug)
    if not item:
        return ""
    pdf_abs = _pdf_path_for_item(vault, item)
    if not pdf_abs or not os.path.isfile(pdf_abs):
        return ""
    try:
        import quick_dip
        text = quick_dip._pdftotext(pdf_abs, 1, 8)
        return (text or "").strip()[:PDF_EXCERPT_CHARS]
    except Exception:
        return ""


def _chunk_for_page(vault, rel, per_page_limit, pdf_fallback=False):
    body = _read(os.path.join(vault, rel), per_page_limit)
    if not body.strip():
        return "", ""
    slug = os.path.splitext(os.path.basename(rel))[0]
    extra = ""
    if pdf_fallback and rel.startswith(("wiki/papers/", "wiki/sources/")) and _wiki_body_thin(body):
        excerpt = _pdf_excerpt_for_slug(vault, slug)
        if excerpt:
            extra = (
                "\n\n#### PDF excerpt (fallback — chart text thin; cite [[{slug}]] not raw PDF)\n"
                "{text}"
            ).format(slug=slug, text=excerpt)
    return body + extra, slug


def _pick_context_pages(vault, question, scope="all", paper_slugs=None, theme_slugs=None):
    paper_slugs = [s for s in (paper_slugs or []) if s]
    theme_slugs = [s for s in (theme_slugs or []) if s]
    pages = []

    targeted_slugs = list(paper_slugs)
    if theme_slugs:
        for slug in _papers_matching_themes(vault, theme_slugs):
            if slug not in targeted_slugs:
                targeted_slugs.append(slug)

    if targeted_slugs or theme_slugs:
        scope_index = _paper_scope_index(vault) if scope != "all" else {}
        for slug in targeted_slugs:
            if not _slug_in_scope(slug, scope, scope_index):
                continue
            rel = _wiki_page_for_slug(vault, slug)
            if os.path.isfile(os.path.join(vault, rel)):
                pages.append(rel)
        for ts in theme_slugs:
            rel = "wiki/themes/{}.md".format(ts)
            if os.path.isfile(os.path.join(vault, rel)):
                pages.append(rel)
        return pages

    all_papers = _all_chart_paper_pages(vault, scope=scope)
    picked = _grep_relevant(vault, question, all_papers, top=8, scope=scope)
    if not picked:
        picked = all_papers[:6]
    return picked


def build_query_prompt(
    vault, question, scope="all", paper_slugs=None, theme_slugs=None, pdf_fallback=False
):
    scope_note = {
        "all": "All charted papers (keyword-matched subset below).",
        "verified": "Only Deep dive papers (human-verified).",
        "needs_review": "Only Quick dip papers (LLM-ingested, awaiting review).",
        "uncharted": "Only Uncharted papers (metadata/abstract on chart; not LLM-ingested).",
    }.get(scope, "")
    paper_slugs = paper_slugs or []
    theme_slugs = theme_slugs or []
    if paper_slugs:
        scope_note += " Focus papers: {}.".format(", ".join(paper_slugs))
    if theme_slugs:
        scope_note += " Focus themes: {} (includes theme hub + linked papers).".format(
            ", ".join(theme_slugs))

    index = _read(os.path.join(vault, "index.md"), 6000)
    overview = _read(os.path.join(vault, "wiki", "overview.md"), 4000)
    picked = _pick_context_pages(
        vault, question, scope=scope, paper_slugs=paper_slugs, theme_slugs=theme_slugs
    )
    targeted = bool(paper_slugs or theme_slugs)
    per_page_limit = 8000 if targeted else 5000

    chunks = []
    sources_used = []
    pdf_sources = []
    for rel in picked:
        chunk, slug = _chunk_for_page(vault, rel, per_page_limit, pdf_fallback=pdf_fallback)
        if not chunk.strip():
            continue
        sources_used.append(slug)
        if "#### PDF excerpt" in chunk:
            pdf_sources.append(slug)
        chunks.append("### [[{slug}]] ({path})\n{body}".format(slug=slug, path=rel, body=chunk))

    context = "\n\n".join(chunks)
    pdf_note = ""
    if pdf_fallback and pdf_sources:
        pdf_note = " PDF excerpts included for thin pages: {}.".format(", ".join(pdf_sources))
    return (
        """You are answering a question about a research wiki (Portolan).
Use ONLY the text below — chart wiki pages{pdf_note}
Every factual claim MUST cite the source page as a [[page-slug]] wikilink (slug = filename without .md).
Label anything not grounded in the context as **[external]**.
If the provided pages lack evidence, say so explicitly.

Scope: {scope_note}
Sources included in this prompt: {sources_list}

## Index (catalog)
{index}

## Overview
{overview}

## Chart pages (your evidence)
{context}

## Question
{question}

## Answer
(use [[wikilinks]] for citations)
""".format(
            pdf_note=pdf_note,
            scope_note=scope_note,
            sources_list=", ".join(sources_used) if sources_used else "(none)",
            index=index or "(no index.md)",
            overview=overview or "(no overview.md)",
            context=context or "(no matching chart pages — cannot answer from the wiki)",
            question=question,
        ),
        sources_used,
    )


def run_query(
    vault,
    question,
    model="qwen3:32b",
    ollama_url=None,
    provider_kind="local",
    frontier_provider=None,
    scope="all",
    paper_slugs=None,
    theme_slugs=None,
    pdf_fallback=False,
):
    vault = os.path.abspath(vault)
    prompt, sources_used = build_query_prompt(
        vault, question, scope=scope, paper_slugs=paper_slugs, theme_slugs=theme_slugs,
        pdf_fallback=pdf_fallback,
    )
    messages = [
        {
            "role": "system",
            "content": (
                "Faithful research wiki assistant. Answer only from provided chart pages. "
                "Cite with [[page-slug]] wikilinks for every claim."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    t0 = time.time()
    result = llm_client.chat(
        provider_kind, model, messages,
        ollama_url=ollama_url, frontier_provider=frontier_provider,
        think=False, temperature=0.3, num_predict=2000,
    )
    elapsed_s = round(time.time() - t0, 1)
    answer = result.get("content", "")
    resolving = llm_grounding.load_resolving_slugs(vault)
    answer, _proposed = llm_grounding.sanitize_wikilinks(answer, resolving)
    return {
        "question": question,
        "answer": answer,
        "model": model,
        "provider_kind": provider_kind,
        "elapsed_s": elapsed_s,
        "scope": scope,
        "paper_slugs": paper_slugs or [],
        "theme_slugs": theme_slugs or [],
        "sources_used": sources_used,
        "pdf_fallback": bool(pdf_fallback),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--question", required=True)
    ap.add_argument("--model", default=os.environ.get("PORTOLAN_LLM_MODEL", "qwen3:32b"))
    ap.add_argument("--ollama-url", default=os.environ.get("OLLAMA_URL"))
    ap.add_argument("--provider", choices=["local", "frontier"], default="local")
    ap.add_argument("--frontier-provider", default="anthropic")
    ap.add_argument("--scope", choices=["all", "verified", "needs_review", "uncharted"], default="all")
    ap.add_argument("--papers", default="", help="Comma-separated paper slugs to query")
    ap.add_argument("--themes", default="", help="Comma-separated theme slugs to query")
    ap.add_argument("--pdf-fallback", action="store_true")
    args = ap.parse_args()
    paper_slugs = [s.strip() for s in args.papers.split(",") if s.strip()]
    theme_slugs = [s.strip() for s in args.themes.split(",") if s.strip()]
    out = run_query(
        args.vault, args.question, model=args.model,
        ollama_url=args.ollama_url, provider_kind=args.provider,
        frontier_provider=args.frontier_provider,
        scope=args.scope,
        paper_slugs=paper_slugs or None,
        theme_slugs=theme_slugs or None,
        pdf_fallback=args.pdf_fallback,
    )
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
