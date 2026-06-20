#!/usr/bin/env python3
"""Per-vault dock definitions — shared by map_channel and SCUBA manager."""

import os
import re

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

DEFAULT_DOCKS = [
    {
        "id": "my-portfolio",
        "emoji": "⚓",
        "name": "My Portfolio",
        "description": "Your research papers and output",
        "raw_path": "raw/papers",
        "profile": "portfolio",
        "extensions": ["pdf"],
        "auto_file": "auto_papers.json",
        "auto_key": "P_AUTO",
    },
    {
        "id": "lit-review",
        "emoji": "🌊",
        "name": "Literature Review",
        "description": "Field papers to read, skim, and connect",
        "raw_path": "raw/literature",
        "profile": "ingest",
        "extensions": ["pdf", "md", "txt"],
        "auto_file": "auto_sources.json",
        "auto_key": "S_AUTO",
        "source_type": "paper",
    },
    {
        "id": "dive-log",
        "emoji": "🤿",
        "name": "Dive Log",
        "description": "Meeting transcripts, session notes, lab discussions",
        "raw_path": "raw/dive-log",
        "profile": "ingest",
        "extensions": ["txt", "md", "pdf", "vtt", "srt"],
        "auto_file": "auto_sources.json",
        "auto_key": "S_AUTO",
        "source_type": "transcript",
    },
    {
        "id": "ideas",
        "emoji": "💡",
        "name": "Ideas & Notes",
        "description": "Sketches, quick captures, research notes",
        "raw_path": "raw/notes/inbox",
        "profile": "ingest",
        "extensions": ["md", "txt"],
        "auto_file": "auto_sources.json",
        "auto_key": "S_AUTO",
        "source_type": "note",
    },
]

# Legacy dock paths still honored when reading stats from old vaults.
LEGACY_RAW_PATHS = {
    "dive-log": ["raw/transcripts", "raw/dive-log"],
    "lab-memory": ["raw/transcripts"],
}


def docks_yaml_path(vault):
    return os.path.join(vault, "builder", "docks.yaml")


def _slugify(name):
    base = name.lower().strip()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return base or "dock"


def seed_docks(vault, write=True):
    """Write default docks.yaml and create raw/ folders."""
    if yaml is None:
        raise RuntimeError("PyYAML required for docks.yaml")
    path = docks_yaml_path(vault)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {"docks": [dict(d) for d in DEFAULT_DOCKS]}
    if write:
        with open(path, "w") as f:
            f.write("# Vault docks — edit by hand or add via SCUBA UI.\n")
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
    for dock in DEFAULT_DOCKS:
        os.makedirs(os.path.join(vault, dock["raw_path"]), exist_ok=True)
    return data["docks"]


def load_docks(vault, create_if_missing=True):
    """Load docks for a vault; seed defaults on first access."""
    if yaml is None:
        return [dict(d) for d in DEFAULT_DOCKS]
    path = docks_yaml_path(vault)
    if not os.path.exists(path):
        if create_if_missing and vault and os.path.isdir(vault):
            return seed_docks(vault)
        return [dict(d) for d in DEFAULT_DOCKS]
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    return data.get("docks", [])


def save_docks(vault, docks):
    if yaml is None:
        raise RuntimeError("PyYAML required")
    path = docks_yaml_path(vault)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("# Vault docks — edit by hand or add via SCUBA UI.\n")
        yaml.safe_dump({"docks": docks}, f, default_flow_style=False, sort_keys=False)


def get_dock(vault, dock_id, create_if_missing=True):
    for dock in load_docks(vault, create_if_missing=create_if_missing):
        if dock.get("id") == dock_id:
            return dock
    return None


def list_visible_docks(vault, create_if_missing=True):
    return load_docks(vault, create_if_missing=create_if_missing)


def dock_to_channel(dock):
    """Normalize dock record for map_channel / channel_registry."""
    ch = dict(dock)
    ch.setdefault("extensions", ["pdf"])
    if isinstance(ch["extensions"], list):
        ch["extensions"] = [
            e if e.startswith(".") else ".{}".format(e.lstrip("."))
            for e in ch["extensions"]
        ]
    return ch


def load_channel_map(vault):
    """Return {channel_id: channel_config} for map_channel."""
    return {d["id"]: dock_to_channel(d) for d in load_docks(vault)}


def add_custom_dock(vault, name, emoji="📁", description="", profile="ingest", extensions=None):
    """Create a user dock: folder under raw/ + entry in docks.yaml."""
    docks = load_docks(vault)
    slug = _slugify(name)
    existing_ids = {d["id"] for d in docks}
    if slug in existing_ids:
        n = 2
        while "{}-{}".format(slug, n) in existing_ids:
            n += 1
        slug = "{}-{}".format(slug, n)
    raw_path = "raw/{}".format(slug)
    exts = extensions or (["pdf"] if profile == "portfolio" else ["md", "txt", "pdf"])
    dock = {
        "id": slug,
        "emoji": emoji,
        "name": name.strip(),
        "description": description or "Custom dock",
        "raw_path": raw_path,
        "profile": profile,
        "extensions": exts,
        "auto_file": "auto_papers.json" if profile == "portfolio" else "auto_sources.json",
        "auto_key": "P_AUTO" if profile == "portfolio" else "S_AUTO",
    }
    if profile == "ingest":
        dock["source_type"] = "note"
    docks.append(dock)
    save_docks(vault, docks)
    os.makedirs(os.path.join(vault, raw_path), exist_ok=True)
    entries_dir = os.path.join(vault, "builder", "entries", slug)
    os.makedirs(entries_dir, exist_ok=True)
    return dock


def resolve_raw_dirs(vault, dock):
    """Primary raw path plus legacy aliases for artifact counting."""
    paths = [dock.get("raw_path", "")]
    dock_id = dock.get("id", "")
    for legacy in LEGACY_RAW_PATHS.get(dock_id, []):
        if legacy not in paths:
            paths.append(legacy)
    return [p for p in paths if p]
