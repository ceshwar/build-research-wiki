"""Reef channel definitions — routing artifacts to raw/ subfolders."""

from pathlib import Path
from typing import Dict, List, Optional

import yaml

BACKEND_DIR = Path(__file__).resolve().parents[2]
CHANNELS_PATH = BACKEND_DIR / "config" / "channels.yaml"


class ChannelRegistry:
    def __init__(self):
        self._channels = self._load()

    def _load(self):
        # type: () -> List[dict]
        with open(CHANNELS_PATH) as f:
            data = yaml.safe_load(f)
        return data.get("channels", [])

    def list_channels(self):
        return list(self._channels)

    def get(self, channel_id):
        # type: (str) -> Optional[dict]
        for ch in self._channels:
            if ch["id"] == channel_id:
                return ch
        return None

    def resolve_dir(self, vault_path, channel_id):
        # type: (Path, str) -> Path
        ch = self.get(channel_id)
        if not ch:
            raise KeyError("Unknown channel: {}".format(channel_id))
        dest = vault_path / ch["raw_path"]
        dest.mkdir(parents=True, exist_ok=True)
        return dest

    def is_portfolio(self, channel_id):
        ch = self.get(channel_id)
        return ch and ch.get("profile") == "portfolio"

    def channel_stats(self, vault_path, channel_id, known_pdfs=None, known_files=None):
        # type: (Path, str, Optional[set], Optional[set]) -> dict
        ch = self.get(channel_id)
        if not ch:
            raise KeyError(channel_id)

        raw_dir = vault_path / ch["raw_path"]
        exts = {e.lower().lstrip(".") for e in ch.get("extensions", [])}
        artifacts = []
        if raw_dir.exists():
            for f in raw_dir.iterdir():
                if f.is_file() and f.suffix.lower().lstrip(".") in exts:
                    artifacts.append(f.name)

        pending = 0
        if ch.get("profile") == "portfolio" and known_pdfs is not None:
            pending = sum(1 for a in artifacts if a.endswith(".pdf") and a not in known_pdfs)
        elif ch.get("profile") == "ingest" and known_files is not None:
            pending = sum(1 for a in artifacts if a not in known_files)
        elif ch.get("profile") == "ingest":
            pending = len(artifacts)

        return {
            "id": ch["id"],
            "name": ch["name"],
            "description": ch.get("description", ""),
            "profile": ch["profile"],
            "raw_path": ch["raw_path"],
            "artifact_count": len(artifacts),
            "pending": pending,
        }


channel_registry = ChannelRegistry()
