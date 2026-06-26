"""Run wiki query jobs."""

import json
import sys
from pathlib import Path

from app.services.process_manager import process_manager
from app.services.settings_service import resolve_stage
from app.services.vault_manager import VaultManager

REPO_ROOT = Path(__file__).resolve().parents[4]


class QueryService:
    def __init__(self, vault_manager):
        # type: (VaultManager) -> None
        self.vaults = vault_manager

    def run_query(
        self,
        vault_id,
        question,
        provider_override=None,
        model_override=None,
        scope="all",
        paper_slugs=None,
        theme_slugs=None,
        pdf_fallback=False,
    ):
        vault_path = self.vaults.resolve_path(vault_id)
        provider_kind, model, ollama_url, frontier_provider = resolve_stage("query")
        if provider_override in ("local", "frontier"):
            provider_kind = provider_override
        if model_override:
            model = model_override
        if scope not in ("all", "verified", "needs_review", "uncharted"):
            scope = "all"
        paper_slugs = paper_slugs or []
        theme_slugs = theme_slugs or []

        script = REPO_ROOT / "builder" / "wiki_query.py"
        cmd = [
            sys.executable,
            str(script),
            "--vault",
            str(vault_path),
            "--question",
            question,
            "--model",
            model,
            "--provider",
            provider_kind,
            "--scope",
            scope,
        ]
        if paper_slugs:
            cmd.extend(["--papers", ",".join(paper_slugs)])
        if theme_slugs:
            cmd.extend(["--themes", ",".join(theme_slugs)])
        if pdf_fallback:
            cmd.append("--pdf-fallback")
        if ollama_url:
            cmd.extend(["--ollama-url", ollama_url])
        if frontier_provider and provider_kind == "frontier":
            cmd.extend(["--frontier-provider", frontier_provider])

        job_id = process_manager.start(
            job_type="query",
            vault_id=vault_id,
            command=cmd,
            cwd=str(REPO_ROOT),
        )
        return job_id, model, provider_kind

    def read_query_result(self, job_id):
        from app.services.process_manager import process_manager
        job = process_manager.get(job_id)
        if not job or job.get("status") != "completed":
            return None
        log_path = job.get("log_file")
        if not log_path:
            return None
        try:
            text = Path(log_path).read_text()
            start = text.rfind("{")
            if start == -1:
                return None
            return json.loads(text[start:])
        except (json.JSONDecodeError, OSError):
            return None
