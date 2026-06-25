"""Load Portolan LLM provider settings (Ollama default: qwen3:32b on GPU tunnel)."""
import os
from functools import lru_cache
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "llm.yaml"


@lru_cache(maxsize=1)
def load_llm_config():
    data = {}
    if _CONFIG_PATH.is_file():
        with open(_CONFIG_PATH) as f:
            data = yaml.safe_load(f) or {}
    stages = data.get("stages") or {}
    default_model = os.environ.get("PORTOLAN_LLM_MODEL") or data.get("default_model") or "qwen3:32b"
    return {
        "ollama_url": os.environ.get("OLLAMA_URL") or data.get("ollama_url") or "http://127.0.0.1:11500",
        "default_model": default_model,
        "embedding_model": data.get("embedding_model") or "nomic-embed-text:latest",
        "think": bool(data.get("think", False)),
        "stages": {
            "deep_dive": stages.get("deep_dive") or default_model,
            "charting": stages.get("charting") or default_model,
            "query": stages.get("query") or default_model,
        },
    }
