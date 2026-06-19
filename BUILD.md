# BUILD — the deterministic builder

This is **optional**. It covers one specific pattern: generating a **paper-portfolio map**
(papers organized by research theme, plus the concept/entity pages around them) from a single
data file — idempotently, so it can run from a script or cron. If you only want the LLM-driven
ingest workflow, ignore this file; see [README.md](README.md) and [CLAUDE.md](CLAUDE.md).

```bash
python3 builder/build.py        # (re)build papers/themes/concepts/entities + index.md (idempotent)
```

- Full docs, file-by-file: **[builder/README.md](builder/README.md)**
- **Edit per vault:** `builder/data.py` (your corpus) and `builder/deepdives/<slug>.md` (deep-dive text)
- **Never generated (hand-maintained):** `wiki/overview.md`, `wiki/syntheses/`, `log.md`, `CLAUDE.md`, this file
- **Scaffold a new vault from this engine:** `python3 builder/new_vault.py /path/to/NewVault "Name"`
- PDF text extraction (optional): `python3 builder/extract_pdfs.py` (needs `poppler`)

The builder auto-detects the vault it lives in and exits 0 when healthy (no red links) / 1
otherwise, so it drops straight into cron, launchd, or CI. See [CLAUDE.md](CLAUDE.md) §10 for
how this fits the wiki schema.
