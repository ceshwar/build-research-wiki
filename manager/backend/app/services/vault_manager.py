"""Vault + channel orchestration."""

import importlib.util
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from app.services.channel_registry import channel_registry

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent.parent
BUILDER_DIR = REPO_ROOT / "builder"
CONFIG_PATH = BACKEND_DIR / "config" / "vaults.yaml"


class VaultManager:
    def __init__(self) -> None:
        self._vaults = self._load_config()

    def _load_config(self) -> List[dict]:
        with open(CONFIG_PATH) as f:
            data = yaml.safe_load(f)
        return data.get("vaults", [])

    def list_vaults(self) -> List[dict]:
        return [self._enrich(v) for v in self._vaults]

    def get_vault(self, vault_id: str) -> dict:
        for v in self._vaults:
            if v["id"] == vault_id:
                return self._enrich(v)
        raise KeyError("Unknown vault: {}".format(vault_id))

    def resolve_path(self, vault_id: str) -> Path:
        vault = self.get_vault(vault_id)
        return Path(vault["path"])

    def _known_pdfs(self, vault_path):
        known = set()
        data_path = vault_path / "builder" / "data.py"
        if data_path.exists():
            mod = self._load_data_module(data_path)
            for p in getattr(mod, "P", []):
                for pdf in p.get("pdfs", []):
                    known.add(pdf)
                    known.add(os.path.basename(pdf))
        for auto_name, key in [("auto_papers.py", "P_AUTO"), ("auto_lab_papers.py", "P_LAB_AUTO")]:
            auto_path = vault_path / "builder" / auto_name
            if auto_path.exists():
                mod = self._load_data_module(auto_path)
                for p in getattr(mod, key, []):
                    for pdf in p.get("pdfs", []):
                        known.add(pdf)
                        known.add(os.path.basename(pdf))
        return known

    def _known_channel_files(self, vault_path, channel_id):
        known = set()
        auto_path = vault_path / "builder" / "auto_sources.py"
        if auto_path.exists():
            mod = self._load_data_module(auto_path)
            for s in getattr(mod, "S_AUTO", []):
                if s.get("channel") != channel_id:
                    continue
                sf = s.get("source_file", "")
                if sf:
                    known.add(sf)
                    known.add(os.path.basename(sf))
        return known

    def _enrich(self, vault: dict) -> dict:
        path = REPO_ROOT / vault["path"]
        stats = self._stats(path)
        return {
            "id": vault["id"],
            "name": vault["name"],
            "path": str(path),
            **stats,
        }

    def _chart_completion(self, vault_path: Path, channel_stats: List[dict]) -> dict:
        if not (vault_path / "builder" / "data.py").exists():
            return {"totals": {}, "by_channel": {}}
        if str(BUILDER_DIR) not in sys.path:
            sys.path.insert(0, str(BUILDER_DIR))
        try:
            import completion
        except ImportError:
            return {"totals": {}, "by_channel": {}}
        pending_map = {c["id"]: c.get("pending", 0) for c in channel_stats}
        return completion.assess_vault(str(vault_path), pending_map)

    def _stats(self, vault_path: Path) -> dict:
        known = self._known_pdfs(vault_path)
        paper_count = 0
        theme_count = 0

        data_path = vault_path / "builder" / "data.py"
        if data_path.exists():
            mod = self._load_data_module(data_path)
            paper_count = len(getattr(mod, "P", []))
            theme_count = len(getattr(mod, "THEMES", {}))
            for auto_name, key in [("auto_papers.py", "P_AUTO"), ("auto_lab_papers.py", "P_LAB_AUTO")]:
                auto_path = vault_path / "builder" / auto_name
                if auto_path.exists():
                    auto_mod = self._load_data_module(auto_path)
                    paper_count += len(getattr(auto_mod, key, []))

        channels = []
        total_artifacts = 0
        total_pending = 0
        for ch in channel_registry.list_channels():
            if ch.get("profile") == "ingest":
                known_ch = self._known_channel_files(vault_path, ch["id"])
                cs = channel_registry.channel_stats(
                    vault_path, ch["id"], known_files=known_ch)
            else:
                cs = channel_registry.channel_stats(vault_path, ch["id"], known_pdfs=known)
            channels.append(cs)
            total_artifacts += cs["artifact_count"]
            total_pending += cs["pending"]

        completion = self._chart_completion(vault_path, channels)
        totals = completion.get("totals", {})
        by_channel = completion.get("by_channel", {})
        for cs in channels:
            ch_report = by_channel.get(cs["id"], {})
            counts = ch_report.get("counts", {})
            cs.update({
                "on_chart": counts.get("on_chart", 0),
                "scaffolded": counts.get("scaffolded", 0),
                "charted": counts.get("charted", 0),
                "processed": counts.get("processed", 0),
                "needs_review": counts.get("scaffolded", 0) + counts.get("charted", 0),
                "needs_attention": [
                    {"slug": a["slug"], "title": a["title"], "status": a["status"]}
                    for a in ch_report.get("needs_attention", [])[:8]
                ],
            })

        last_build = self._last_build_time(vault_path)
        return {
            "artifact_count": total_artifacts,
            "paper_count": paper_count,
            "theme_count": theme_count,
            "last_build": last_build,
            "pending_artifacts": total_pending,
            "on_chart": totals.get("on_chart", paper_count),
            "scaffolded_count": totals.get("scaffolded", 0),
            "charted_count": totals.get("charted", 0),
            "processed_count": totals.get("processed", 0),
            "needs_review_count": totals.get("scaffolded", 0) + totals.get("charted", 0),
            "channels": channels,
            # legacy fields
            "pdf_count": next((c["artifact_count"] for c in channels if c["id"] == "my-portfolio"), 0),
        }

    def _load_data_module(self, data_path: Path):
        spec = importlib.util.spec_from_file_location("vault_data", data_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _last_build_time(self, vault_path: Path) -> Optional[str]:
        wiki_files = glob.glob(str(vault_path / "wiki" / "**" / "*.md"), recursive=True)
        if not wiki_files:
            return None
        latest = max(os.path.getmtime(f) for f in wiki_files)
        return datetime.fromtimestamp(latest).isoformat(timespec="minutes")

    def ensure_channel_dir(self, vault_id, channel_id):
        # type: (str, str) -> Path
        vault_path = self.resolve_path(vault_id)
        return channel_registry.resolve_dir(vault_path, channel_id)

    def has_builder(self, vault_id: str) -> bool:
        return self.build_plan(vault_id) is not None

    def build_plan(self, vault_id, mode="auto"):
        vault_path = self.resolve_path(vault_id)
        data_path = vault_path / "builder" / "data.py"
        local_build = vault_path / "builder" / "build.py"
        engine_build = REPO_ROOT / "builder" / "build.py"

        extra = []
        if mode == "full":
            extra = ["--full"]
        elif mode == "incremental":
            extra = ["--incremental"]

        if local_build.exists():
            return {
                "command": [sys.executable, "builder/build.py"] + extra,
                "cwd": str(vault_path),
            }

        if data_path.exists() and engine_build.exists():
            return {
                "command": [
                    sys.executable,
                    str(engine_build),
                    "--vault",
                    str(vault_path),
                ] + extra,
                "cwd": str(REPO_ROOT),
            }

        return None

    def map_plan(self, vault_id, channel_id="my-portfolio"):
        # type: (str, str) -> Optional[dict]
        vault_path = self.resolve_path(vault_id)
        data_path = vault_path / "builder" / "data.py"
        engine_map = REPO_ROOT / "builder" / "map_channel.py"
        ch = channel_registry.get(channel_id)
        if not ch:
            return None

        extra = ["--vault", str(vault_path), "--channel", channel_id]

        if data_path.exists() and engine_map.exists():
            return {
                "command": [sys.executable, str(engine_map)] + extra,
                "cwd": str(REPO_ROOT),
            }

        return None

    def ingest_status_plan(self, vault_id, channel_id):
        # type: (str, str) -> Optional[dict]
        vault_path = self.resolve_path(vault_id)
        ch = channel_registry.get(channel_id)
        if not ch or ch.get("profile") != "ingest":
            return None
        engine = REPO_ROOT / "builder" / "channel_status.py"
        return {
            "command": [
                sys.executable,
                str(engine),
                "--vault",
                str(vault_path),
                "--channel",
                channel_id,
                "--raw-path",
                ch["raw_path"],
            ],
            "cwd": str(REPO_ROOT),
        }

    def extract_plan(self, vault_id):
        vault_path = self.resolve_path(vault_id)
        local_extract = vault_path / "builder" / "extract_pdfs.py"
        if local_extract.exists():
            return {
                "command": [sys.executable, "builder/extract_pdfs.py"],
                "cwd": str(vault_path),
            }
        return None
