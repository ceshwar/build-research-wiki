#!/usr/bin/env python3
"""Slugs removed from the chart — hidden from corpus until re-mapped."""

import json
import os


def _path(builder_dir):
    return os.path.join(builder_dir, "off_chart.json")


def load(builder_dir):
    path = _path(builder_dir)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def save(builder_dir, data):
    os.makedirs(builder_dir, exist_ok=True)
    with open(_path(builder_dir), "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def slugs_for(builder_dir, channel_id):
    ch = load(builder_dir).get(channel_id, {})
    if isinstance(ch, list):
        return set(ch)
    return set(ch.get("slugs", []))


def add_slug(builder_dir, channel_id, slug):
    data = load(builder_dir)
    ch = data.setdefault(channel_id, {"slugs": []})
    if isinstance(ch, list):
        ch = {"slugs": ch}
        data[channel_id] = ch
    slugs = ch.setdefault("slugs", [])
    if slug not in slugs:
        slugs.append(slug)
    save(builder_dir, data)


def remove_slug(builder_dir, channel_id, slug):
    data = load(builder_dir)
    ch = data.get(channel_id, {})
    if isinstance(ch, list):
        slugs = ch
    else:
        slugs = ch.get("slugs", [])
    if slug not in slugs:
        return False
    kept = [s for s in slugs if s != slug]
    data[channel_id] = {"slugs": kept}
    save(builder_dir, data)
    return True


def is_off_chart(builder_dir, channel_id, slug):
    return slug in slugs_for(builder_dir, channel_id)


def filter_entries(builder_dir, channel_id, entries):
    off = slugs_for(builder_dir, channel_id)
    if not off:
        return list(entries)
    return [e for e in entries if e.get("slug") not in off]
