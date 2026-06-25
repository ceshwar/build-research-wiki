"""Run LLM Deep Dive jobs (deep_dive_llm.py → build.py)."""

import sys
from pathlib import Path

from app.services.channel_registry import channel_registry
from app.services.process_manager import process_manager
from app.services.settings_service import resolve_stage
from app.services.vault_manager import VaultManager

REPO_ROOT = Path(__file__).resolve().parents[4]


class DeepDiveService:
    def __init__(self, vault_manager):
        # type: (VaultManager) -> None
        self.vaults = vault_manager

    def deep_dive_plan(self, vault_id, channel_id, slug, provider_override=None, model_override=None):
        vault_path = self.vaults.resolve_path(vault_id)
        ch = channel_registry.get(channel_id, vault_path)
        if not ch:
            raise KeyError(f"Unknown channel: {channel_id}")

        provider_kind, model, ollama_url, frontier_provider = resolve_stage("deep_dive")
        if provider_override in ("local", "frontier"):
            provider_kind = provider_override
        if model_override:
            model = model_override

        script = REPO_ROOT / "builder" / "deep_dive_llm.py"
        cmd = [
            sys.executable,
            str(script),
            "--vault",
            str(vault_path),
            "--channel",
            channel_id,
            "--slug",
            slug,
            "--model",
            model,
            "--provider",
            provider_kind,
        ]
        if ollama_url:
            cmd.extend(["--ollama-url", ollama_url])
        if frontier_provider and provider_kind == "frontier":
            cmd.extend(["--frontier-provider", frontier_provider])

        build_plan = self.vaults.build_plan(vault_id, mode="incremental")
        steps = [("deep_dive", cmd, str(REPO_ROOT))]
        if build_plan:
            steps.append(("build", build_plan["command"], build_plan["cwd"]))
        return steps, model, provider_kind

    def run_deep_dive(self, vault_id, channel_id, slug, provider_override=None, model_override=None):
        steps, model, provider_kind = self.deep_dive_plan(
            vault_id, channel_id, slug, provider_override, model_override)
        job_id = process_manager.start_chain(
            job_type="deep_dive",
            vault_id=vault_id,
            steps=steps,
            label=f"Deep Dive ({model}) — {slug}",
        )
        return job_id, model, provider_kind

    def run_deep_dive_batch(self, vault_id, channel_id, slugs, provider_override=None, model_override=None):
        vault_path = self.vaults.resolve_path(vault_id)
        provider_kind, model, ollama_url, frontier_provider = resolve_stage("deep_dive")
        if provider_override in ("local", "frontier"):
            provider_kind = provider_override
        if model_override:
            model = model_override

        script = REPO_ROOT / "builder" / "deep_dive_llm.py"
        steps = []
        for slug in slugs:
            cmd = [
                sys.executable, str(script),
                "--vault", str(vault_path),
                "--channel", channel_id,
                "--slug", slug,
                "--model", model,
                "--provider", provider_kind,
            ]
            if ollama_url:
                cmd.extend(["--ollama-url", ollama_url])
            if frontier_provider and provider_kind == "frontier":
                cmd.extend(["--frontier-provider", frontier_provider])
            steps.append((f"deep_dive:{slug}", cmd, str(REPO_ROOT)))

        build_plan = self.vaults.build_plan(vault_id, mode="incremental")
        if build_plan:
            steps.append(("build", build_plan["command"], build_plan["cwd"]))

        job_id = process_manager.start_chain(
            job_type="deep_dive_batch",
            vault_id=vault_id,
            steps=steps,
            label=f"Deep Dive batch ({len(slugs)} papers)",
        )
        return job_id, model, provider_kind
