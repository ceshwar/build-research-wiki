#!/usr/bin/env python3
"""Automated LLM Deep Dive — writes builder/entries/ + builder/deepdives/, marks verification.

    python3 builder/deep_dive_llm.py --vault /path --channel my-portfolio --slug paper-slug
    python3 builder/deep_dive_llm.py --vault /path --channel my-portfolio --all-needs-work
"""
import argparse
import json
import os
import re
import subprocess
import sys

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))
if BUILDER_DIR not in sys.path:
    sys.path.insert(0, BUILDER_DIR)

import completion
import ingest_prompt
import llm_client
import llm_grounding
import verification
from docks_util import load_channel_map
from slug_util import canonical_slug

PORTFOLIO_SECTIONS = [
    "Authors",
    "Research question",
    "Method",
    "Findings",
    "Claims & evidence",
    "Limitations",
    "Contributes to",
]


def pdftotext(pdf_path, max_pages=12):
    try:
        out = subprocess.check_output(
            ["pdftotext", "-f", "1", "-l", str(max_pages), pdf_path, "-"],
            stderr=subprocess.DEVNULL,
        )
        return out.decode("utf-8", errors="replace")
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""


def load_themes(vault):
    data_path = os.path.join(vault, "builder", "data.py")
    if not os.path.isfile(data_path):
        return []
    data = completion._load_module(data_path)
    themes = getattr(data, "THEMES", {})
    return [(slug, meta[0]) for slug, meta in sorted(themes.items())]


def resolve_pdf_path(vault, item, channels):
    pdfs = item.get("pdfs") or []
    if not pdfs:
        return None
    src = pdfs[0]
    if "/" not in src:
        raw_path = channels.get(item.get("channel", "my-portfolio"), {}).get("raw_path", "raw/papers")
        src = os.path.join(raw_path, src)
    abs_path = os.path.join(vault, src)
    return abs_path if os.path.isfile(abs_path) else None


def build_json_prompt(title, pdf_text, themes, locked):
    theme_lines = "\n".join(f"- {s} — {t}" for s, t in themes)
    locked_block = llm_grounding.format_locked_block(locked)
    section_names = ", ".join(PORTFOLIO_SECTIONS)
    return f"""You are filling a Portolan Deep Dive for a research paper. Use ONLY the PDF text below.
Every field must include an evidence_span: a short verbatim quote from the PDF text (not paraphrase).
Do not invent facts, links, or themes.

{locked_block}

**Allowed theme slugs** (pick 1–3 for "themes"; use exact slugs only):
{theme_lines}

Return a single JSON object with this shape:
{{
  "themes": ["theme-slug"],
  "one_liner": {{"text": "one sentence", "evidence_span": "quote from PDF"}},
  "sections": [
    {{"name": "Authors", "text": "...", "evidence_span": "quote"}},
    {{"name": "Research question", "text": "...", "evidence_span": "quote"}}
  ],
  "proposed_concepts": ["concept-slug-for-human-review"]
}}

Required section names (exact): {section_names}
- proposed_concepts: concepts worth a wiki page but NOT in allowed themes — no [[wikilinks]] in text unless they resolve to allowed themes.
- Do not contradict locked metadata.

**Paper title:** {title}

**PDF text (excerpt):**
---
{pdf_text[:12000]}
---
"""


def parse_llm_output(text):
    """Legacy markdown fallback."""
    themes = []
    one_liner = ""
    deepdive_body = ""

    theme_m = re.search(r"(?is)##\s*Themes[^\n]*\n(.*?)(?=\n##\s|\Z)", text)
    if theme_m:
        line = theme_m.group(1).strip().split("\n")[0]
        for raw in re.findall(r"\[\[([^\]|]+)", line):
            slug = canonical_slug(raw.strip()) or raw.strip().lower()
            if slug and slug not in themes:
                themes.append(slug)

    one_m = re.search(r"(?is)##\s*One-liner\s*\n(.*?)(?=\n##\s|\Z)", text)
    if one_m:
        one_liner = one_m.group(1).strip().split("\n")[0].strip()

    dd_m = re.search(r"(?is)##\s*Deep dive\s*\n(.*)", text)
    if dd_m:
        deepdive_body = dd_m.group(1).strip()

    return themes, one_liner, deepdive_body


def process_json_response(data, pdf_text, vault, locked):
    allowed_themes = llm_grounding.load_allowed_theme_slugs(vault)
    resolving = llm_grounding.load_resolving_slugs(vault)
    allowed_links = resolving | allowed_themes

    themes = llm_grounding.filter_themes(data.get("themes"), allowed_themes)
    dropped = {"themes": [], "sections": [], "one_liner": False}

    one = data.get("one_liner") or {}
    one_text = (one.get("text") or "").strip()
    one_span = (one.get("evidence_span") or "").strip()
    if one_text and not llm_grounding.evidence_grounds(one_span, pdf_text):
        dropped["one_liner"] = True
        one_text = ""

    sections_out = []
    for sec in data.get("sections") or []:
        name = (sec.get("name") or "").strip()
        text = (sec.get("text") or "").strip()
        span = (sec.get("evidence_span") or "").strip()
        if not name or not text:
            continue
        if name.lower() == "authors":
            text = llm_grounding.authors_section_text(locked, text)
            if locked.get("authors"):
                span = span or text[:80]
        if not llm_grounding.evidence_grounds(span, pdf_text):
            if name.lower() == "authors" and locked.get("authors"):
                pass
            else:
                dropped["sections"].append(name)
                continue
        sections_out.append({"name": name, "text": text})

    body = llm_grounding.assemble_deep_dive_body(sections_out, allowed_links)
    proposed_raw = list(data.get("proposed_concepts") or [])
    proposed = []
    for raw in proposed_raw:
        slug = canonical_slug(str(raw).strip()) or str(raw).strip().lower()
        if slug and slug not in allowed_links and slug not in proposed:
            proposed.append(slug)

    return themes, one_text, body, proposed, dropped


def _read_existing_abstract(entry_path):
    if not entry_path or not os.path.isfile(entry_path):
        return ""
    parsed = completion._parse_entry(entry_path)
    return (parsed.get("abstract") or parsed.get("summary") or "").strip()


def write_entry(vault, channel_id, slug, themes, abstract, one_liner):
    rel = f"builder/entries/{channel_id}/{slug}.md"
    abs_path = os.path.join(vault, rel)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    theme_line = ", ".join(f"[[{t}]]" for t in themes) if themes else "<!-- themes pending -->"
    lines = [theme_line, "", "## Abstract", "", abstract or "—", "", "## One-liner", "", one_liner or "—", "", "## My notes", ""]
    with open(abs_path, "w") as f:
        f.write("\n".join(lines))
    return rel


def write_deepdive(vault, slug, body):
    dd_dir = os.path.join(vault, "builder", "deepdives")
    os.makedirs(dd_dir, exist_ok=True)
    path = os.path.join(dd_dir, slug + ".md")
    with open(path, "w") as f:
        f.write(body.strip() + "\n")
    return path


def enrichment_source_for(model, provider_kind):
    if provider_kind == "frontier":
        return "frontier"
    low = (model or "").lower()
    if "32b" in low:
        return "local-32b"
    return "local-custom"


def run_deep_dive(
    vault,
    channel_id,
    slug,
    model="qwen3:32b",
    ollama_url=None,
    provider_kind="local",
    frontier_provider=None,
    think=False,
    dry_run=False,
):
    vault = os.path.abspath(vault)
    channels = load_channel_map(vault)
    corpus = [e for e in ingest_prompt._full_corpus(vault) if e.get("channel") == channel_id]
    item = next((e for e in corpus if e["slug"] == slug), None)
    if not item:
        raise ValueError(f"Paper not on chart: {slug}")

    pdf_path = resolve_pdf_path(vault, item, channels)
    if not pdf_path:
        raise FileNotFoundError(f"No PDF for {slug}")

    pdf_text = pdftotext(pdf_path)
    if not pdf_text.strip():
        raise RuntimeError("pdftotext failed — install poppler (brew install poppler)")

    title = item.get("title") or slug
    locked = llm_grounding.locked_metadata(item)
    themes_meta = load_themes(vault)
    prompt = build_json_prompt(title, pdf_text, themes_meta, locked)

    messages = [
        {"role": "system", "content": "You are a faithful research assistant. Return only valid JSON grounded in the PDF."},
        {"role": "user", "content": prompt},
    ]

    if dry_run:
        return {"slug": slug, "dry_run": True, "prompt_chars": len(prompt)}

    result = llm_client.chat_json(
        provider_kind, model, messages,
        ollama_url=ollama_url, frontier_provider=frontier_provider, think=think,
        num_predict=2400,
    )
    payload = result.get("json")
    if not payload:
        raise RuntimeError("LLM returned empty JSON")

    parsed_themes, one_liner, deepdive_body, proposed, dropped = process_json_response(
        payload, pdf_text, vault, locked,
    )
    if not deepdive_body:
        content = llm_grounding.sanitize_llm_output(result.get("content") or "")
        parsed_themes, one_liner, deepdive_body = parse_llm_output(content)
        allowed_themes = llm_grounding.load_allowed_theme_slugs(vault)
        parsed_themes = llm_grounding.filter_themes(parsed_themes, allowed_themes)
        resolving = llm_grounding.load_resolving_slugs(vault)
        deepdive_body, link_props = llm_grounding.sanitize_wikilinks(
            deepdive_body, resolving | allowed_themes,
        )
        proposed = list(proposed) + link_props

    entry_rel = item.get("entry") or item.get("note") or f"builder/entries/{channel_id}/{slug}.md"
    entry_abs = completion._resolve_entry_path(vault, entry_rel, channel_id)
    abstract = _read_existing_abstract(entry_abs) or completion._parse_entry(entry_abs).get("summary", "")

    entry_rel = write_entry(vault, channel_id, slug, parsed_themes, abstract, one_liner)
    dd_path = write_deepdive(vault, slug, deepdive_body)

    builder_dir = os.path.join(vault, "builder")
    proposed_path = llm_grounding.save_proposed_links(builder_dir, channel_id, slug, proposed)
    src = enrichment_source_for(model, provider_kind)
    verification.mark_llm_enriched(builder_dir, channel_id, slug, model, enrichment_source=src)

    import registry
    for json_name, default_ch in verification.REGISTRY_FILES:
        entries = registry.load(builder_dir, json_name)
        for row in entries:
            if row.get("slug") != slug:
                continue
            if (row.get("channel") or default_ch) != channel_id:
                continue
            row["one"] = one_liner
            row["themes"] = parsed_themes
            row["entry"] = entry_rel
            registry.save(builder_dir, json_name, entries)
            break

    return {
        "slug": slug,
        "model": model,
        "provider_kind": provider_kind,
        "enrichment_source": src,
        "entry": entry_rel,
        "deepdive": os.path.relpath(dd_path, vault),
        "eval_count": result.get("eval_count"),
        "grounding_dropped": dropped,
        "proposed_links": os.path.relpath(proposed_path, vault) if proposed_path else None,
    }


def slugs_needing_work(vault, channel_id):
    out = []
    for item in ingest_prompt._full_corpus(vault):
        if item.get("channel") != channel_id:
            continue
        assessed = completion.assess_entry(vault, {**item, "profile": item.get("profile", "portfolio")})
        if assessed["status"] in ingest_prompt.NEEDS_WORK:
            out.append(item["slug"])
    return out


def main():
    ap = argparse.ArgumentParser(description="LLM Deep Dive for Portolan")
    ap.add_argument("--vault", required=True)
    ap.add_argument("--channel", default="my-portfolio")
    ap.add_argument("--slug", help="Single paper slug")
    ap.add_argument("--all-needs-work", action="store_true")
    ap.add_argument("--model", default=os.environ.get("PORTOLAN_LLM_MODEL", "qwen3:32b"))
    ap.add_argument("--ollama-url", default=os.environ.get("OLLAMA_URL"))
    ap.add_argument("--provider", choices=["local", "frontier"], default="local")
    ap.add_argument("--frontier-provider", choices=["anthropic", "openai"], default="anthropic")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    slugs = [args.slug] if args.slug else []
    if args.all_needs_work:
        slugs = slugs_needing_work(args.vault, args.channel)
    if not slugs:
        print("No slugs to process.", file=sys.stderr)
        return 1

    results = []
    for slug in slugs:
        print(f"Deep Dive: {slug} ({args.model})…", flush=True)
        try:
            r = run_deep_dive(
                args.vault, args.channel, slug,
                model=args.model,
                ollama_url=args.ollama_url,
                provider_kind=args.provider,
                frontier_provider=args.frontier_provider,
                dry_run=args.dry_run,
            )
            results.append(r)
            print(json.dumps(r, indent=2))
        except Exception as e:
            print(f"FAILED {slug}: {e}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
