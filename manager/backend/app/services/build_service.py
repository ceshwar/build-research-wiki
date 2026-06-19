"""Thin wrapper around existing builder scripts."""

from app.services.process_manager import process_manager
from app.services.vault_manager import VaultManager


class BuildService:
    def __init__(self, vault_manager):
        # type: (VaultManager) -> None
        self.vaults = vault_manager

    def rebuild_wiki(self, vault_id, mode="auto"):
        # type: (str, str) -> str
        plan = self.vaults.build_plan(vault_id, mode=mode)
        if not plan:
            raise FileNotFoundError(
                "No builder available for vault '{0}'".format(vault_id)
            )

        return process_manager.start(
            job_type="build",
            vault_id=vault_id,
            command=plan["command"],
            cwd=plan["cwd"],
        )

    def extract_pdfs(self, vault_id):
        # type: (str) -> str
        plan = self.vaults.extract_plan(vault_id)
        if not plan:
            raise FileNotFoundError(
                "PDF extraction not available for vault '{0}'".format(vault_id)
            )

        return process_manager.start(
            job_type="extract",
            vault_id=vault_id,
            command=plan["command"],
            cwd=plan["cwd"],
        )
