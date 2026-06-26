#!/usr/bin/env python3
"""Human verification state for chart entries (registry rows + verification.json overrides).

LLM Deep Dive fills content but does not imply accuracy — ``human_verified`` must be set
explicitly after a human or frontier-model review. Hand-curated ``status: mapped`` rows in
data.py default to verified unless ``llm_enriched`` is set.
"""
import json
import os
from datetime import date

import registry

REGISTRY_FILES = [
    ("auto_papers.json", "my-portfolio"),
    ("auto_lab_papers.json", "lab-portfolio"),
    ("auto_sources.json", None),
]


def _store_path(builder_dir):
    return os.path.join(builder_dir, "verification.json")


def load_overrides(builder_dir):
    path = _store_path(builder_dir)
    if not os.path.isfile(path):
        return {}
    with open(path) as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def save_overrides(builder_dir, data):
    os.makedirs(builder_dir, exist_ok=True)
    with open(_store_path(builder_dir), "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def effective(entry, assessed_status=None, overrides=None):
    """Resolved verification fields for one chart entry."""
    overrides = overrides if overrides is not None else {}
    slug = entry.get("slug", "")
    ov = overrides.get(slug, {}) if slug else {}

    llm_enriched = bool(entry.get("llm_enriched") or ov.get("llm_enriched"))
    llm_model = (entry.get("llm_model") or ov.get("llm_model") or "").strip()
    enrichment_source = (
        ov.get("enrichment_source") or entry.get("enrichment_source") or ""
    ).strip()
    if not enrichment_source and llm_enriched:
        enrichment_source = "local-32b" if "32b" in llm_model.lower() else "local-custom"
    elif not enrichment_source and entry.get("status") == "quick-dip":
        enrichment_source = "quick-dip"
    elif not enrichment_source and entry.get("status") == "mapped":
        enrichment_source = "human"

    if "human_verified" in ov:
        human_verified = bool(ov["human_verified"])
    elif entry.get("human_verified") is not None:
        human_verified = bool(entry["human_verified"])
    elif llm_enriched:
        human_verified = False
    elif entry.get("status") == "mapped":
        human_verified = True
    else:
        human_verified = False

    verified_at = (ov.get("verified_at") or entry.get("verified_at") or "").strip()
    verified_by = (ov.get("verified_by") or entry.get("verified_by") or "").strip()

    status = assessed_status or entry.get("completion_status") or ""
    needs_human_verification = llm_enriched and not human_verified
    if human_verified:
        territory = "charted"
    elif llm_enriched:
        territory = "quick_dip"
    else:
        territory = "uncharted"

    return {
        "human_verified": human_verified,
        "needs_human_verification": needs_human_verification,
        "llm_enriched": llm_enriched,
        "llm_model": llm_model,
        "enrichment_source": enrichment_source,
        "territory": territory,
        "verified_at": verified_at,
        "verified_by": verified_by,
    }


def _sync_registry_row(builder_dir, channel_id, slug, fields):
    for json_name, default_channel in REGISTRY_FILES:
        entries = registry.load(builder_dir, json_name)
        changed = False
        for item in entries:
            ch = item.get("channel") or default_channel
            if item.get("slug") != slug or ch != channel_id:
                continue
            for key, val in fields.items():
                if val is None:
                    item.pop(key, None)
                else:
                    item[key] = val
            changed = True
            break
        if changed:
            registry.save(builder_dir, json_name, entries)
            return True
    return False


def set_human_verified(vault_path, channel_id, slug, verified, verified_by="human"):
    """Mark a paper human-verified (or revoke). Persists to verification.json + auto registry."""
    builder_dir = os.path.join(os.path.abspath(vault_path), "builder")
    overrides = load_overrides(builder_dir)
    rec = dict(overrides.get(slug, {}))
    rec["human_verified"] = bool(verified)
    if verified:
        rec["verified_at"] = date.today().isoformat()
        rec["verified_by"] = verified_by or "human"
    else:
        rec.pop("verified_at", None)
        rec.pop("verified_by", None)
    overrides[slug] = rec
    save_overrides(builder_dir, overrides)

    sync_fields = {
        "human_verified": bool(verified),
        "verified_at": rec.get("verified_at"),
        "verified_by": rec.get("verified_by"),
    }
    if not verified:
        sync_fields = {"human_verified": False, "verified_at": None, "verified_by": None}
    _sync_registry_row(builder_dir, channel_id, slug, sync_fields)
    return rec


def mark_llm_enriched(builder_dir, channel_id, slug, model, enrichment_source=None):
    """Record that an entry was LLM-enriched (unverified until review)."""
    builder_dir = os.path.abspath(builder_dir)
    src = enrichment_source or ("local-32b" if "32b" in (model or "").lower() else "local-custom")
    overrides = load_overrides(builder_dir)
    rec = dict(overrides.get(slug, {}))
    rec.update({
        "llm_enriched": True,
        "llm_model": model,
        "llm_enriched_at": date.today().isoformat(),
        "enrichment_source": src,
        "human_verified": False,
    })
    rec.pop("verified_at", None)
    rec.pop("verified_by", None)
    overrides[slug] = rec
    save_overrides(builder_dir, overrides)
    _sync_registry_row(builder_dir, channel_id, slug, {
        "llm_enriched": True,
        "llm_model": model,
        "llm_enriched_at": rec["llm_enriched_at"],
        "enrichment_source": src,
        "human_verified": False,
        "verified_at": None,
        "verified_by": None,
    })
