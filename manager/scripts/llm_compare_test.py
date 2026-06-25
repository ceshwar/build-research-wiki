#!/usr/bin/env python3
"""Side-by-side Deep Dive comparison for Ollama models → HTML report."""

import json
import os
import subprocess
import sys
import time
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VAULT = ROOT / "examples/minimal-vault"
OUT_DIR = ROOT / "manager/scripts/.llm-compare"
OLLAMA = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11500")

PAPER = {
    "slug": "popular-feed-audit",
    "pdf": VAULT / "raw/papers/2502.20491v3.pdf",
    "gold_deepdive": VAULT / "builder/deepdives/popular-feed-audit.md",
    "title": "Examining Algorithmic Curation on Social Media: An Empirical Audit of Reddit's r/popular Feed",
}

THEMES = [
    ("algorithmic-ai-audits", "Algorithmic and AI Audits"),
    ("social-media-online-communities", "Social Media & Online Communities"),
    ("computational-social-science", "Computational Social Science"),
    ("digital-governance", "Digital Governance"),
    ("healthy-online-behavior", "Healthy Online Behavior"),
]

MODELS = [
    {"id": "qwen3:32b", "label": "Qwen3 32B (dense — current default)", "no_think": True},
    {
        "id": "qwen3:30b-a3b-instruct-2507-q4_K_M",
        "label": "Qwen3 30B-A3B MoE instruct (candidate)",
        "no_think": True,
    },
]

SECTIONS = [
    "Authors", "Research question", "Method", "Findings",
    "Claims & evidence", "Limitations", "Contributes to",
]


def pdftotext(pdf: Path, max_pages: int = 12) -> str:
    try:
        out = subprocess.check_output(
            ["pdftotext", "-f", "1", "-l", str(max_pages), str(pdf), "-"],
            stderr=subprocess.DEVNULL,
        )
        return out.decode("utf-8", errors="replace")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def build_prompt(pdf_text: str) -> str:
    theme_lines = "\n".join(f"- [[{s}]] — {t}" for s, t in THEMES)
    return f"""You are filling a Portolan Deep Dive for a research paper. Use ONLY the PDF text below. Do not invent facts.

**Allowed themes** (pick 1–3 for line 1 of the entry):
{theme_lines}

**Output format** — markdown with these sections exactly:
## Themes (line 1 only)
[[theme-slug]] [[theme-slug]]

## One-liner
One sentence contribution.

## Deep dive
For each: **Section name.** content
Sections: {", ".join(SECTIONS)}

Use [[wikilinks]] for concepts mentioned. Flag uncertainty. No placeholder text.

**Paper title:** {PAPER["title"]}

**PDF text (excerpt):**
---
{pdf_text[:12000]}
---
"""


def ollama_chat(model: str, prompt: str, no_think: bool) -> dict:
    import urllib.request

    system = "You are a faithful research assistant. Summarize only from the provided PDF text."

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.2, "num_predict": 1200},
    }).encode()

    start = time.time()
    req = urllib.request.Request(
        f"{OLLAMA}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode())
    elapsed = time.time() - start
    content = data.get("message", {}).get("content", "")
    eval_count = data.get("eval_count")
    eval_duration = data.get("eval_duration")
    tps = None
    if eval_count and eval_duration:
        tps = round(eval_count / (eval_duration / 1e9), 1)
    return {
        "content": content,
        "elapsed_s": round(elapsed, 1),
        "eval_count": eval_count,
        "eval_duration_ns": eval_duration,
        "tokens_per_sec": tps,
    }


def render_html(results: list, gold: str, pdf_chars: int, pending=None) -> str:
    pending = pending or []
    cards = []
    for r in results:
        cards.append(f"""
        <article class="card">
          <header>
            <h2>{html.escape(r["label"])}</h2>
            <p class="meta"><code>{html.escape(r["model"])}</code> · {r["elapsed_s"]}s
            {f' · ~{r["eval_count"]} tokens out' if r.get("eval_count") else ''}</p>
          </header>
          <pre class="output">{html.escape(r["content"])}</pre>
        </article>
        """)

    pending_html = ""
    if pending:
        names = ", ".join(html.escape(p["id"]) for p in pending)
        pending_html = f'<p class="note"><strong>Still running:</strong> {names} — refresh to update.</p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="refresh" content="20" />
  <title>Portolan LLM Deep Dive comparison</title>
  <style>
    :root {{
      --navy: #1b2a4a; --accent: #ea580c; --bg: #f8fafc; --card: #fff;
      --muted: #64748b; --border: #e2e8f0;
    }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: system-ui, sans-serif; margin: 0; background: var(--bg); color: #1e293b; }}
    header.hero {{
      background: linear-gradient(115deg, #141f36, #243552);
      color: #fff; padding: 1.5rem 2rem;
    }}
    header.hero h1 {{ margin: 0 0 .25rem; font-size: 1.35rem; }}
    header.hero p {{ margin: 0; color: #cbd5e1; font-size: .9rem; }}
    .layout {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; padding: 1rem 2rem 2rem; max-width: 1400px; margin: 0 auto; }}
    @media (max-width: 1100px) {{ .layout {{ grid-template-columns: 1fr; }} }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }}
    .card header {{ padding: .75rem 1rem; border-bottom: 1px solid var(--border); background: #fff; }}
    .card h2 {{ margin: 0; font-size: 1rem; color: var(--navy); }}
    .meta {{ margin: .25rem 0 0; font-size: .75rem; color: var(--muted); }}
    pre.output {{
      margin: 0; padding: 1rem; font-size: .72rem; line-height: 1.45;
      white-space: pre-wrap; word-break: break-word; max-height: 520px; overflow: auto;
      background: #f1f5f9;
    }}
    .gold {{ grid-column: 1 / -1; border-color: var(--accent); }}
    .gold header {{ background: rgba(234,88,12,.06); }}
    .note {{ padding: 0 2rem 1rem; color: var(--muted); font-size: .85rem; max-width: 1400px; margin: 0 auto; }}
  </style>
</head>
<body>
  <header class="hero">
    <h1>Deep Dive model comparison</h1>
    <p>{html.escape(PAPER["title"])} · PDF excerpt {pdf_chars:,} chars · GPU Ollama via SSH tunnel · Quick Dip stays deterministic</p>
  </header>
  <p class="note">Compare structure, factual accuracy, and themes vs the hand-authored gold deep dive below.
  Default target: <strong>qwen3:8b</strong> (speed) vs <strong>qwen3:32b</strong> (quality on GPU).</p>
  {pending_html}
  <div class="layout">
    <article class="card gold">
      <header><h2>Gold (hand-authored)</h2><p class="meta">builder/deepdives/popular-feed-audit.md</p></header>
      <pre class="output">{html.escape(gold)}</pre>
    </article>
    {"".join(cards)}
  </div>
</body>
</html>"""


def main() -> int:
    if not PAPER["pdf"].exists():
        print("PDF not found:", PAPER["pdf"], file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_text = pdftotext(PAPER["pdf"])
    if not pdf_text.strip():
        print("pdftotext failed — install poppler (brew install poppler)", file=sys.stderr)
        return 1

    prompt = build_prompt(pdf_text)
    gold = PAPER["gold_deepdive"].read_text() if PAPER["gold_deepdive"].exists() else ""

    results = []
    for m in MODELS:
        print(f"Running {m['id']}…", flush=True)
        try:
            out = ollama_chat(m["id"], prompt, m["no_think"])
            results.append({**m, "model": m["id"], **out, "error": None})
            print(f"  done in {out['elapsed_s']}s", flush=True)
        except Exception as e:
            results.append({**m, "model": m["id"], "content": str(e), "elapsed_s": 0, "error": str(e)})
            print(f"  FAILED: {e}", flush=True)
        # Incremental HTML so browser can refresh during long runs
        html_path = OUT_DIR / "index.html"
        html_path.write_text(render_html(results, gold, len(pdf_text), pending=MODELS[len(results):]))

    (OUT_DIR / "results.json").write_text(json.dumps(results, indent=2))
    html_path = OUT_DIR / "index.html"
    html_path.write_text(render_html(results, gold, len(pdf_text)))
    print(f"\nWrote {html_path}")
    print(f"Open: http://127.0.0.1:8765/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
