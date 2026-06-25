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


def _wiki_pages(vault, max_pages=12):
    wiki = os.path.join(vault, "wiki")
    pages = []
    for root, _dirs, files in os.walk(wiki):
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(root, name), vault)
            pages.append(rel.replace("\\", "/"))
            if len(pages) >= max_pages:
                return pages
    return pages


def _grep_relevant(vault, question, pages, top=6):
    terms = [t.lower() for t in re.findall(r"[a-zA-Z]{4,}", question)]
    scored = []
    for rel in pages:
        text = _read(os.path.join(vault, rel), limit=12000).lower()
        score = sum(text.count(t) for t in terms)
        if score > 0:
            scored.append((score, rel))
    scored.sort(reverse=True)
    return [rel for _s, rel in scored[:top]]


def build_query_prompt(vault, question):
    index = _read(os.path.join(vault, "index.md"), 6000)
    overview = _read(os.path.join(vault, "wiki", "overview.md"), 4000)
    pages = _wiki_pages(vault, max_pages=40)
    picked = _grep_relevant(vault, question, pages)
    if not picked:
        picked = [p for p in pages if p.startswith("wiki/papers/")][:4]

    chunks = []
    for rel in picked:
        body = _read(os.path.join(vault, rel), 3500)
        slug = os.path.splitext(os.path.basename(rel))[0]
        chunks.append(f"### [[{slug}]] ({rel})\n{body}")

    context = "\n\n".join(chunks)
    return f"""You are answering a question about a research wiki (Portolan). Use ONLY the context below.
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


def run_query(vault, question, model="qwen3:32b", ollama_url=None, provider_kind="local", frontier_provider=None):
    vault = os.path.abspath(vault)
    prompt = build_query_prompt(vault, question)
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
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--question", required=True)
    ap.add_argument("--model", default=os.environ.get("PORTOLAN_LLM_MODEL", "qwen3:32b"))
    ap.add_argument("--ollama-url", default=os.environ.get("OLLAMA_URL"))
    ap.add_argument("--provider", choices=["local", "frontier"], default="local")
    ap.add_argument("--frontier-provider", default="anthropic")
    args = ap.parse_args()
    out = run_query(
        args.vault, args.question, model=args.model,
        ollama_url=args.ollama_url, provider_kind=args.provider,
        frontier_provider=args.frontier_provider,
    )
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
