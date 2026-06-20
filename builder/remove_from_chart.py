#!/usr/bin/env python3
"""Remove a charted paper from the map (PDF stays in raw/)."""

import os
import sys

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))
if BUILDER_DIR not in sys.path:
    sys.path.insert(0, BUILDER_DIR)

import ingest_prompt
import off_chart
import registry
from docks_util import load_channel_map


def _find_entry(vault, channel_id, slug):
    for item in ingest_prompt._full_corpus(vault):
        if item.get("channel") == channel_id and item.get("slug") == slug:
            return item
    return None


def _remove_from_auto(builder_dir, auto_file, channel_id, slug):
    entries = registry.load(builder_dir, auto_file)
    kept = [e for e in entries if not (e.get("slug") == slug and (e.get("channel") or "my-portfolio") == channel_id)]
    if len(kept) != len(entries):
        registry.save(builder_dir, auto_file, kept)
        return True
    return False


def remove(vault, channel_id, slug, dry_run=False):
    """Unchart slug: registry + generated pages; PDF remains in raw/."""
    vault = os.path.abspath(vault)
    builder_dir = os.path.join(vault, "builder")
    channels = load_channel_map(vault)
    ch = channels.get(channel_id)
    if not ch:
        raise ValueError("Unknown channel: {}".format(channel_id))

    entry = _find_entry(vault, channel_id, slug)
    if not entry:
        raise KeyError("Paper '{}' not on chart for {}".format(slug, channel_id))

    profile = ch.get("profile", "portfolio")
    auto_file = ch.get("auto_file", "auto_papers.json" if profile == "portfolio" else "auto_sources.json")
    wiki_folder = "wiki/papers" if profile == "portfolio" else "wiki/sources"

    paths_to_delete = []
    entry_rel = entry.get("entry") or entry.get("note", "")
    if entry_rel:
        paths_to_delete.append(os.path.join(vault, entry_rel))
    paths_to_delete.append(os.path.join(vault, wiki_folder, slug + ".md"))
    deep = os.path.join(builder_dir, "deepdives", slug + ".md")
    if os.path.isfile(deep):
        paths_to_delete.append(deep)

    if dry_run:
        return {
            "slug": slug,
            "channel_id": channel_id,
            "removed_auto": True,
            "deleted": [p for p in paths_to_delete if os.path.isfile(p)],
        }

    removed_auto = _remove_from_auto(builder_dir, auto_file, channel_id, slug)
    off_chart.add_slug(builder_dir, channel_id, slug)

    deleted = []
    for path in paths_to_delete:
        if os.path.isfile(path):
            os.remove(path)
            deleted.append(path)

    return {
        "slug": slug,
        "channel_id": channel_id,
        "removed_auto": removed_auto,
        "deleted": deleted,
    }


def main():
    vault = os.path.dirname(BUILDER_DIR)
    channel_id = "my-portfolio"
    dry_run = "--dry-run" in sys.argv

    if "--vault" in sys.argv:
        vault = os.path.abspath(sys.argv[sys.argv.index("--vault") + 1])
    if "--channel" in sys.argv:
        channel_id = sys.argv[sys.argv.index("--channel") + 1]
    if "--slug" not in sys.argv:
        sys.exit("usage: remove_from_chart.py --vault PATH --channel ID --slug SLUG")
    slug = sys.argv[sys.argv.index("--slug") + 1]

    result = remove(vault, channel_id, slug, dry_run=dry_run)
    print("removed: {} ({})".format(result["slug"], result["channel_id"]))
    if result["deleted"]:
        for p in result["deleted"]:
            print("  deleted: {}".format(p))
    return 0


if __name__ == "__main__":
    sys.exit(main())
