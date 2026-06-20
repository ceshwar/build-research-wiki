"""Vault + channel orchestration."""

import glob
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from app.services.channel_registry import channel_registry  # inserts builder/ onto sys.path
import registry  # builder/registry.py — JSON read for generated Quick Dip registries

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent.parent
BUILDER_DIR = REPO_ROOT / "builder"
CONFIG_PATH = BACKEND_DIR / "config" / "vaults.yaml"
USER_CONFIG_PATH = BACKEND_DIR / "config" / "vaults.user.yaml"


class VaultManager:
    def __init__(self) -> None:
        self.reload()

    def reload(self) -> None:
        self._vaults = self._load_all()

    def _load_all(self) -> List[dict]:
        builtin = self._load_yaml(CONFIG_PATH)
        user = self._load_yaml(USER_CONFIG_PATH)
        seen = {v["id"] for v in builtin}
        merged = list(builtin)
        for v in user:
            if v["id"] not in seen:
                merged.append(v)
                seen.add(v["id"])
        return merged

    def _load_yaml(self, path: Path) -> List[dict]:
        if not path.exists():
            return []
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        vaults = data.get("vaults", []) or []
        for v in vaults:
            v.setdefault("user_added", path == USER_CONFIG_PATH)
        return vaults

    def _save_user_vaults(self, vaults: List[dict]) -> None:
        USER_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(USER_CONFIG_PATH, "w") as f:
            yaml.safe_dump({"vaults": vaults}, f, default_flow_style=False, sort_keys=False)

    def _resolve_vault_path(self, vault: dict) -> Path:
        p = Path(vault["path"]).expanduser()
        if not p.is_absolute():
            p = REPO_ROOT / p
        return p.resolve()

    def _obsidian_config_path(self) -> Optional[Path]:
        home = Path.home()
        if sys.platform == "darwin":
            cfg = home / "Library/Application Support/obsidian/obsidian.json"
        elif sys.platform == "win32":
            appdata = os.environ.get("APPDATA", "")
            cfg = Path(appdata) / "obsidian/obsidian.json" if appdata else None
        else:
            cfg = home / ".config/obsidian/obsidian.json"
        return cfg if cfg and cfg.exists() else None

    def _load_obsidian_vaults(self) -> Dict[str, dict]:
        cfg = self._obsidian_config_path()
        if not cfg:
            return {}
        try:
            with open(cfg) as f:
                data = json.load(f)
        except (OSError, ValueError):
            return {}
        return data.get("vaults", {}) or {}

    def _obsidian_link_meta(self, vault: dict, vault_path: Path) -> dict:
        """Resolve Obsidian URI target: registered vault id + path links open in."""
        registered = self._load_obsidian_vaults()
        override_id = vault.get("obsidian_vault_id")
        if override_id:
            meta = registered.get(str(override_id), {})
            link_path = meta.get("path")
            return {
                "obsidian_vault_id": str(override_id),
                "obsidian_links_ok": bool(link_path),
                "obsidian_link_path": str(Path(link_path).resolve()) if link_path else None,
            }
        for vid, meta in registered.items():
            p = meta.get("path")
            if not p:
                continue
            try:
                if Path(p).expanduser().resolve() == vault_path:
                    return {
                        "obsidian_vault_id": vid,
                        "obsidian_links_ok": True,
                        "obsidian_link_path": str(vault_path),
                    }
            except OSError:
                continue
        return {
            "obsidian_vault_id": None,
            "obsidian_links_ok": False,
            "obsidian_link_path": None,
        }

    def _slugify(self, name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        return slug or "vault"

    def _unique_id(self, base: str) -> str:
        existing = {v["id"] for v in self._vaults}
        if base not in existing:
            return base
        n = 2
        while "{}-{}".format(base, n) in existing:
            n += 1
        return "{}-{}".format(base, n)

    def validate_path(self, path_str: str) -> dict:
        p = Path(path_str).expanduser()
        if not p.is_absolute():
            p = (REPO_ROOT / p).resolve()
        else:
            p = p.resolve()

        if not p.exists():
            return {"ok": False, "path": str(p), "error": "Folder does not exist."}
        if not p.is_dir():
            return {"ok": False, "path": str(p), "error": "Path is not a folder."}

        has_builder = (p / "builder" / "data.py").exists()
        has_wiki = (p / "wiki").is_dir()
        paper_count = 0
        mod = None
        if has_builder:
            try:
                mod = self._load_data_module(p / "builder" / "data.py")
                paper_count = len(getattr(mod, "P", []))
            except Exception:
                pass

        warnings = []
        if not has_builder:
            warnings.append("No builder/data.py — Surface Interval will not work until you add a builder.")
        if not has_wiki:
            warnings.append("No wiki/ folder yet — chart may be empty until you build or ingest.")

        suggested_name = p.name.replace("-", " ").replace("_", " ").title()
        if has_builder and mod:
            vn = getattr(mod, "VAULT", {}).get("name")
            if vn:
                suggested_name = vn

        return {
            "ok": True,
            "path": str(p),
            "has_builder": has_builder,
            "has_wiki": has_wiki,
            "paper_count": paper_count,
            "suggested_name": suggested_name,
            "warnings": warnings,
        }

    def pick_folder(self) -> Optional[str]:
        """Native folder picker (local dev only)."""
        if sys.platform == "darwin":
            script = 'POSIX path of (choose folder with prompt "Select your Obsidian vault folder")'
            result = subprocess.run(
                ["osascript", "-e", script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            if result.returncode != 0:
                return None
            return result.stdout.strip()
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            path = filedialog.askdirectory(title="Select your Obsidian vault folder")
            root.destroy()
            return path or None
        except Exception:
            return None

    def add_vault(self, path_str: str, name: Optional[str] = None) -> dict:
        check = self.validate_path(path_str)
        if not check.get("ok"):
            raise ValueError(check.get("error", "Invalid vault path"))

        p = Path(check["path"])
        display = name.strip() if name else check["suggested_name"]
        base_id = self._slugify(p.name)
        vault_id = self._unique_id(base_id)

        entry = {
            "id": vault_id,
            "name": display,
            "path": str(p),
            "user_added": True,
        }

        user_vaults = self._load_yaml(USER_CONFIG_PATH)
        for v in user_vaults:
            if self._resolve_vault_path(v) == p:
                raise ValueError("This folder is already registered as '{}'.".format(v["name"]))
        user_vaults.append(entry)
        self._save_user_vaults(user_vaults)
        self.reload()
        return self.get_vault(vault_id)

    def remove_vault(self, vault_id: str) -> None:
        user_vaults = self._load_yaml(USER_CONFIG_PATH)
        kept = [v for v in user_vaults if v["id"] != vault_id]
        if len(kept) == len(user_vaults):
            raise KeyError("Only user-added vaults can be removed.")
        self._save_user_vaults(kept)
        self.reload()

    def list_vaults(self) -> List[dict]:
        return [self._enrich(v) for v in self._vaults]

    def resolve_path(self, vault_id: str) -> Path:
        return self._resolve_vault_path(self._vault_by_id(vault_id))

    def _vault_by_id(self, vault_id: str) -> dict:
        for v in self._vaults:
            if v["id"] == vault_id:
                return v
        raise KeyError("Unknown vault: {}".format(vault_id))

    def get_vault(self, vault_id: str) -> dict:
        return self._enrich(self._vault_by_id(vault_id))

    def _known_pdfs(self, vault_path):
        known = set()
        data_path = vault_path / "builder" / "data.py"
        if data_path.exists():
            mod = self._load_data_module(data_path)
            for p in getattr(mod, "P", []):
                for pdf in p.get("pdfs", []):
                    known.add(pdf)
                    known.add(os.path.basename(pdf))
        builder_dir = str(vault_path / "builder")
        for auto_name in ("auto_papers.json", "auto_lab_papers.json"):
            for p in registry.load(builder_dir, auto_name):
                for pdf in p.get("pdfs", []):
                    known.add(pdf)
                    known.add(os.path.basename(pdf))
        return known

    def _known_channel_files(self, vault_path, channel_id):
        known = set()
        for s in registry.load(str(vault_path / "builder"), "auto_sources.json"):
            if s.get("channel") != channel_id:
                continue
            sf = s.get("source_file", "")
            if sf:
                known.add(sf)
                known.add(os.path.basename(sf))
        return known

    def _enrich(self, vault: dict) -> dict:
        path = self._resolve_vault_path(vault)
        stats = self._stats(path)
        return {
            "id": vault["id"],
            "name": vault["name"],
            "path": str(path),
            "user_added": vault.get("user_added", False),
            **self._obsidian_link_meta(vault, path),
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
            builder_dir = str(vault_path / "builder")
            for auto_name in ("auto_papers.json", "auto_lab_papers.json"):
                paper_count += len(registry.load(builder_dir, auto_name))

        channels = []
        total_artifacts = 0
        total_pending = 0
        channel_registry.ensure_vault_docks(vault_path)
        for ch in channel_registry.list_channels(vault_path):
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
                "quick_dip": counts.get("quick_dip", 0),
                "needs_deep_dive": counts.get("needs_deep_dive", 0),
                "scaffolded": counts.get("scaffolded", 0),
                "charted": counts.get("charted", 0),
                "processed": counts.get("processed", 0),
                "needs_review": counts.get("needs_deep_dive", 0) + counts.get("scaffolded", 0),
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
            "quick_dip_count": totals.get("quick_dip", 0),
            "needs_deep_dive_count": totals.get("needs_deep_dive", 0),
            "scaffolded_count": totals.get("scaffolded", 0),
            "charted_count": totals.get("charted", 0),
            "processed_count": totals.get("processed", 0),
            "needs_review_count": totals.get("needs_deep_dive", 0) + totals.get("scaffolded", 0),
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
        ch = channel_registry.get(channel_id, vault_path)
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
        ch = channel_registry.get(channel_id, vault_path)
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
