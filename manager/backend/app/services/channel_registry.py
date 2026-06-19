"""Reef dock definitions — per-vault builder/docks.yaml with global defaults."""

import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent.parent
BUILDER_DIR = REPO_ROOT / "builder"
sys.path.insert(0, str(BUILDER_DIR))

from docks_util import (  # noqa: E402
    DEFAULT_DOCKS,
    add_custom_dock,
    dock_to_channel,
    get_dock,
    list_visible_docks,
    load_docks,
    resolve_raw_dirs,
    seed_docks,
)


class ChannelRegistry:
    def __init__(self):
        self._defaults = [dict(d) for d in DEFAULT_DOCKS]

    def ensure_vault_docks(self, vault_path: Path):
        load_docks(str(vault_path), create_if_missing=True)

    def list_channels(self, vault_path: Optional[Path] = None, include_hidden: bool = False):
        # type: (...) -> List[dict]
        if vault_path:
            self.ensure_vault_docks(vault_path)
            docks = load_docks(str(vault_path), create_if_missing=False)
        else:
            docks = self._defaults
        return [self._public_channel(d) for d in docks]

    def _public_channel(self, dock):
        ch = self._normalize(dock)
        profile = ch["profile"]
        return {
            "id": ch["id"],
            "name": ch["name"],
            "emoji": ch.get("emoji", "📁"),
            "description": ch.get("description", ""),
            "profile": profile,
            "raw_path": ch["raw_path"],
            "extensions": [e.lstrip(".") for e in ch.get("extensions", [])],
            # portfolio: Quick Dip → wiki/papers (supported). ingest: shell only until Phase 3.
            "chart_support": "full" if profile == "portfolio" else "preview",
        }

    def _normalize(self, dock):
        return dock_to_channel(dict(dock))

    def get(self, channel_id, vault_path: Optional[Path] = None):
        # type: (str, Optional[Path]) -> Optional[dict]
        if vault_path:
            self.ensure_vault_docks(vault_path)
            dock = get_dock(str(vault_path), channel_id, create_if_missing=False)
            return self._normalize(dock) if dock else None
        for d in self._defaults:
            if d["id"] == channel_id:
                return self._normalize(d)
        return None

    def resolve_dir(self, vault_path, channel_id):
        # type: (Path, str) -> Path
        ch = self.get(channel_id, vault_path)
        if not ch:
            raise KeyError("Unknown channel: {}".format(channel_id))
        dest = vault_path / ch["raw_path"]
        dest.mkdir(parents=True, exist_ok=True)
        return dest

    def is_portfolio(self, channel_id, vault_path: Optional[Path] = None):
        ch = self.get(channel_id, vault_path)
        return ch and ch.get("profile") == "portfolio"

    def create_dock(self, vault_path: Path, name: str, emoji: str = "📁",
                    description: str = "", profile: str = "ingest"):
        self.ensure_vault_docks(vault_path)
        dock = add_custom_dock(
            str(vault_path), name=name, emoji=emoji,
            description=description, profile=profile,
        )
        return self._public_channel(dock)

    def channel_stats(self, vault_path, channel_id, known_pdfs=None, known_files=None):
        # type: (Path, str, Optional[set], Optional[set]) -> dict
        ch = self.get(channel_id, vault_path)
        if not ch:
            raise KeyError(channel_id)

        exts = {e.lower().lstrip(".") for e in ch.get("extensions", [])}
        artifacts = []
        dock = get_dock(str(vault_path), channel_id, create_if_missing=False) or {}
        for raw_rel in resolve_raw_dirs(str(vault_path), dock):
            raw_dir = vault_path / raw_rel
            if not raw_dir.exists():
                continue
            for f in raw_dir.iterdir():
                if f.is_file() and f.suffix.lower().lstrip(".") in exts:
                    if f.name not in artifacts:
                        artifacts.append(f.name)

        pending = 0
        if ch.get("profile") == "portfolio" and known_pdfs is not None:
            pending = sum(1 for a in artifacts if a.endswith(".pdf") and a not in known_pdfs)
        elif ch.get("profile") == "ingest" and known_files is not None:
            pending = sum(1 for a in artifacts if a not in known_files)
        elif ch.get("profile") == "ingest":
            pending = len(artifacts)

        pub = self._public_channel(dock) if dock else self._public_channel(ch)
        return {
            **pub,
            "artifact_count": len(artifacts),
            "pending": pending,
        }


channel_registry = ChannelRegistry()
