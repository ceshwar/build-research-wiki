#!/usr/bin/env python3
"""Query the wiki — read index + relevant pages, answer with citations."""

import argparse
import json
import os
import re
import sys
import time

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))
if BUILDER_DIR not in sys.path:
    sys.path.insert(0, BUILDER_DIR)

import llm_client
import llm_grounding


def _read(path, limit=8000):
    if not os.path.isfile(path):
        return ""
    with open(path) as f:
        text = f.read()
    return text[:limit]


def _paper_scope_index(vault):
    """slug -> verified (bool), uncharted (bool) for portfolio papers."""
    import completion
    import ingest_prompt

    out = {}
    for item in ingest_prompt._full_corpus(vault):
        assessed = completion.assess_entry(vault, item)
        slug = item.get("slug")
        if not slug:
            continue
        out[slug] = {
            "verified": bool(assessed.get("human_verified")),
            "llm_enriched": bool(assessed.get("llm_enriched")),
            "uncharted": not assessed.get("llm_enriched"),
            "needs_review": bool(assessed.get("llm_enriched")) and not assessed.get("human_verified"),
        }
    return out


def _page_in_scope(rel, scope, scope_index):
    if scope == "all" or not scope_index:
        return True
    if not rel.startswith("wiki/papers/") or not rel.endswith(".md"):
        return True
    slug = os.path.splitext(os.path.basename(rel))[0]
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


def _wiki_pages(vault, max_pages=12, scope="all"):
    scope_index = _paper_scope_index(vault) if scope != "all" else {}
    wiki = os.path.join(vault, "wiki")
    pages = []
    for root, _dirs, files in os.walk(wiki):
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(root, name), vault).replace("\\", "/")
            if not _page_in_scope(rel, scope, scope_index):
                continue
            pages.append(rel)
            if len(pages) >= max_pages:
                return pages
    return pages


def _grep_relevant(vault, question, pages, top=6, scope="all"):
    scope_index = _paper_scope_index(vault) if scope != "all" else {}
    terms = [t.lower() for t in re.findall(r"[a-zA-Z]{4,}", question)]
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


def build_query_prompt(vault, question, scope="all"):
    scope_note = {
        "all": "All charted papers.",
        "verified": "Only Deep dive papers (human-verified).",
        "needs_review": "Only Quick dip papers (LLM-ingested, awaiting review).",
        "uncharted": "Only Uncharted papers (not yet LLM-ingested).",
    }.get(scope, "")
    index = _read(os.path.join(vault, "index.md"), 6000)
    overview = _read(os.path.join(vault, "wiki", "overview.md"), 4000)
    pages = _wiki_pages(vault, max_pages=40, scope=scope)
    picked = _grep_relevant(vault, question, pages, scope=scope)
    if not picked:
        picked = [p for p in pages if p.startswith("wiki/papers/")][:4]

    chunks = []
    for rel in picked:
        body = _read(os.path.join(vault, rel), 3500)
        slug = os.path.splitext(os.path.basename(rel))[0]
        chunks.append(f"### [[{slug}]] ({rel})\n{body}")

    context = "\n\n".join(chunks)
    return f"""You are answering a question about a research wiki (Portolan). Use ONLY the context below.
Scope: {scope_note}
Cite sources as [[page-slug]] wikilinks. Label outside knowledge **[external]**.
If the wiki lacks evidence, say so.

## Index (catalog)
{index or '(no index.md)'}

## Overview
{overview or '(no overview.md)'}

## Relevant pages
{context}

## Question
{question}

## Answer
"""


def run_query(
    vault,
    question,
    model="qwen3:32b",
    ollama_url=None,
    provider_kind="local",
    frontier_provider=None,
    scope="all",
):
    vault = os.path.abspath(vault)
    prompt = build_query_prompt(vault, question, scope=scope)
    messages = [
        {"role": "system", "content": "Faithful research wiki assistant. Cite [[sources]]."},
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
    args = ap.parse_args()
    out = run_query(
        args.vault, args.question, model=args.model,
        ollama_url=args.ollama_url, provider_kind=args.provider,
        frontier_provider=args.frontier_provider,
        scope=args.scope,
    )
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
