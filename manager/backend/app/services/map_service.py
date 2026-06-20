"""Run map_pdfs.py and build.py as a chained surface interval."""

from app.services.channel_registry import channel_registry
from app.services.process_manager import process_manager
from app.services.vault_manager import VaultManager


class MapService:
    def __init__(self, vault_manager):
        # type: (VaultManager) -> None
        self.vaults = vault_manager

    def surface_interval(self, vault_id, channel_id="my-portfolio", build_mode="auto"):
        # type: (str, str, str) -> str
        vault_path = self.vaults.resolve_path(vault_id)
        ch = channel_registry.get(channel_id, vault_path)
        if not ch:
            raise KeyError("Unknown channel: {}".format(channel_id))
        if not self.vaults.has_builder(vault_id):
            raise FileNotFoundError("No builder for vault '{}'".format(vault_id))

        map_plan = self.vaults.map_plan(vault_id, channel_id=channel_id)
        build_plan = self.vaults.build_plan(vault_id, mode=build_mode)
        if not map_plan or not build_plan:
            raise FileNotFoundError("No chart pipeline for '{}'".format(channel_id))

        steps = [
            ("map", map_plan["command"], map_plan["cwd"]),
            ("build", build_plan["command"], build_plan["cwd"]),
        ]

        return process_manager.start_chain(
            job_type="surface_interval",
            vault_id=vault_id,
            steps=steps,
            label="Quick dip — {} / {}".format(vault_path.name, ch["name"]),
        )

    def map_pdfs(self, vault_id, channel_id="my-portfolio"):
        plan = self.vaults.map_plan(vault_id, channel_id=channel_id)
        if not plan:
            raise FileNotFoundError("No mapper for channel '{}'".format(channel_id))
        return process_manager.start(
            job_type="map",
            vault_id=vault_id,
            command=plan["command"],
            cwd=plan["cwd"],
        )

    def rebuild_wiki(self, vault_id, mode="auto"):
        plan = self.vaults.build_plan(vault_id, mode=mode)
        if not plan:
            raise FileNotFoundError("No builder for vault '{}'".format(vault_id))
        return process_manager.start(
            job_type="build",
            vault_id=vault_id,
            command=plan["command"],
            cwd=plan["cwd"],
        )

    def remove_from_chart(self, vault_id, channel_id, slug):
        # type: (str, str, str) -> tuple
        vault_path = self.vaults.resolve_path(vault_id)
        ch = channel_registry.get(channel_id, vault_path)
        if not ch:
            raise KeyError("Unknown channel: {}".format(channel_id))

        import remove_from_chart as rfc  # builder/ on sys.path

        result = rfc.remove(str(vault_path), channel_id, slug)
        job_id = None
        build_plan = self.vaults.build_plan(vault_id, mode="incremental")
        if build_plan:
            job_id = process_manager.start(
                job_type="build",
                vault_id=vault_id,
                command=build_plan["command"],
                cwd=build_plan["cwd"],
            )
        return result, job_id
