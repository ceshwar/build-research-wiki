"""Load and persist Portolan user settings (YAML)."""
import copy
import os
from functools import lru_cache
from pathlib import Path

import yaml

_CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
_DEFAULTS_PATH = _CONFIG_DIR / "settings.yaml"
_USER_PATH = _CONFIG_DIR / "settings.user.yaml"


def _deep_merge(base, override):
    out = copy.deepcopy(base)
    for key, val in (override or {}).items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = val
    return out


def _load_yaml(path):
    if not path.is_file():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def load_settings():
    defaults = _load_yaml(_DEFAULTS_PATH)
    user = _load_yaml(_USER_PATH)
    merged = _deep_merge(defaults, user)
    llm = merged.get("llm") or {}
    models = llm.get("models") or {}
    env_url = os.environ.get("OLLAMA_URL")
    env_model = os.environ.get("PORTOLAN_LLM_MODEL")
    if env_url:
        llm["ollama_url"] = env_url
    if env_model:
        for key in ("deep_dive", "charting", "query"):
            models.setdefault(key, env_model)
    llm["models"] = models
    merged["llm"] = llm
    return merged


def save_settings(patch):
    current = load_settings()
    updated = _deep_merge(current, patch or {})
    _USER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_USER_PATH, "w") as f:
        yaml.dump(updated, f, default_flow_style=False, sort_keys=False)
        f.write("\n")
    load_settings.cache_clear()
    return updated


def settings_for_api():
    s = load_settings()
    llm = s.get("llm") or {}
    models = llm.get("models") or {}
    frontier = llm.get("frontier") or {}
    catalog = llm.get("model_catalog") or [
        "qwen3:8b",
        "qwen3:32b",
        "qwen3:30b-a3b-instruct-2507-q4_K_M",
        "nomic-embed-text",
    ]
    return {
        "view_in": s.get("view_in") or "app",
        "llm": {
            "deep_dive_provider": llm.get("deep_dive_provider") or "local",
            "query_provider": llm.get("query_provider") or "local",
            "ollama_url": llm.get("ollama_url") or "http://127.0.0.1:11500",
            "think": bool(llm.get("think", False)),
            "model_catalog": list(catalog),
            "models": {
                "deep_dive": models.get("deep_dive") or "qwen3:32b",
                "charting": models.get("charting") or "qwen3:8b",
                "query": models.get("query") or "qwen3:32b",
            },
            "frontier": {
                "provider": frontier.get("provider") or "anthropic",
                "deep_dive_model": frontier.get("deep_dive_model") or "claude-sonnet-4-20250514",
                "query_model": frontier.get("query_model") or "claude-sonnet-4-20250514",
            },
        },
    }


def resolve_stage(stage):
    """Return provider_kind, model, ollama_url, frontier_provider for a stage."""
    s = settings_for_api()
    llm = s["llm"]
    provider_key = f"{stage}_provider" if stage in ("deep_dive", "query") else None
    provider_kind = llm.get(provider_key) or "local" if provider_key else "local"
    models = llm["models"]
    frontier = llm["frontier"]
    if provider_kind == "frontier":
        model = frontier.get(f"{stage}_model") or frontier.get("deep_dive_model")
        return provider_kind, model, llm["ollama_url"], frontier.get("provider")
    model = models.get(stage) or models.get("deep_dive") or "qwen3:32b"
    return "local", model, llm["ollama_url"], None
