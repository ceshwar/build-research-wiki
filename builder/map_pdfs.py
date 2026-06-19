#!/usr/bin/env python3
"""Backward-compatible wrapper — use map_channel.py instead.

Maps unmapped PDFs in raw/papers/ (or lab) to builder/entries/, not raw/notes/.
"""
import os
import sys

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BUILDER_DIR)

from map_channel import map_channel, CHANNELS


def map_vault(vault, dry_run=False, papers_subdir="raw/papers",
              auto_file="auto_papers.py", auto_key="P_AUTO", channel=""):
    channel_id = channel or "my-portfolio"
    if channel_id == "lab-portfolio":
        channel_id = "lab-portfolio"
    elif papers_subdir == "raw/lab/papers":
        channel_id = "lab-portfolio"
    return map_channel(vault, channel_id, dry_run=dry_run)


def main():
    vault = os.path.dirname(BUILDER_DIR)
    dry_run = "--dry-run" in sys.argv
    channel_id = "my-portfolio"

    if "--vault" in sys.argv:
        vault = os.path.abspath(sys.argv[sys.argv.index("--vault") + 1])
    if "--channel" in sys.argv:
        channel_id = sys.argv[sys.argv.index("--channel") + 1]
    elif "--papers-dir" in sys.argv:
        sub = sys.argv[sys.argv.index("--papers-dir") + 1]
        if "lab" in sub:
            channel_id = "lab-portfolio"

    print("channel: {} (via map_channel)".format(channel_id))
    mapped = map_channel(vault, channel_id, dry_run=dry_run)
    if mapped:
        print("mapped {} PDF(s){}".format(
            len(mapped), " (dry-run)" if dry_run else " → builder/entries/"))
    else:
        cfg = CHANNELS[channel_id]
        print("no unmapped PDFs in {}".format(cfg["raw_path"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
