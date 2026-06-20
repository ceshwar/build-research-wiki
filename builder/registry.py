#!/usr/bin/env python3
"""Read/write the machine-generated chart registries as JSON.

These registries hold the entries produced by Quick Dip (map_channel) for docked
artifacts. They used to be emitted as executable Python modules (auto_papers.py …)
and `exec`'d on every load — which meant uploaded filenames flowed into generated,
executed code and a stray backslash/quote could corrupt data or break import.

JSON removes both problems: it never executes, and it round-trips arbitrary strings
losslessly. The hand-authored corpus (builder/data.py) stays Python on purpose — it
is trusted, vault-owner-edited config, not machine output fed by uploads.

Legacy `.py` registries are migrated transparently: load() reads them if no JSON
exists yet, and the next save() writes JSON and removes the stale `.py`.
"""
import importlib.util
import json
import os

# json filename -> (legacy .py filename, module-level list variable)
_LEGACY = {
    "auto_papers.json": ("auto_papers.py", "P_AUTO"),
    "auto_lab_papers.json": ("auto_lab_papers.py", "P_LAB_AUTO"),
    "auto_sources.json": ("auto_sources.py", "S_AUTO"),
}


def json_name(auto_file):
    """Normalize a configured auto_file (legacy '.py' or new '.json') to its '.json' name."""
    return os.path.splitext(auto_file)[0] + ".json"


def _legacy_for(jname):
    if jname in _LEGACY:
        return _LEGACY[jname]
    return (os.path.splitext(jname)[0] + ".py", None)


def _load_legacy_py(path, key):
    spec = importlib.util.spec_from_file_location("_legacy_registry", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if key and isinstance(getattr(mod, key, None), list):
        return list(getattr(mod, key))
    # Unknown key: fall back to the first UPPER list attribute.
    for name, val in vars(mod).items():
        if name.isupper() and isinstance(val, list):
            return list(val)
    return []


def load(builder_dir, auto_file):
    """Return the list of entry dicts for a registry. Accepts a '.json' or legacy '.py' name."""
    jname = json_name(auto_file)
    jpath = os.path.join(builder_dir, jname)
    if os.path.exists(jpath):
        with open(jpath) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data.get("entries", [])
        return data if isinstance(data, list) else []
    legacy_py, key = _legacy_for(jname)
    lpath = os.path.join(builder_dir, legacy_py)
    if os.path.exists(lpath):
        return _load_legacy_py(lpath, key)
    return []


def save(builder_dir, auto_file, entries):
    """Write entries as JSON; remove any stale legacy '.py' so it can't shadow the JSON."""
    jname = json_name(auto_file)
    if not os.path.isdir(builder_dir):
        os.makedirs(builder_dir, exist_ok=True)
    with open(os.path.join(builder_dir, jname), "w") as f:
        json.dump(list(entries), f, indent=2, ensure_ascii=False)
        f.write("\n")
    legacy_py, _ = _legacy_for(jname)
    lpath = os.path.join(builder_dir, legacy_py)
    if os.path.exists(lpath):
        os.remove(lpath)
