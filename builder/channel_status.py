#!/usr/bin/env python3
"""Report staged artifacts for an ingest channel (LLM ingest = Phase 3)."""
import os
import sys

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BUILDER_DIR)


def main():
    vault = REPO_ROOT
    channel = "lit-review"
    raw_sub = "raw/literature"

    if "--vault" in sys.argv:
        vault = os.path.abspath(sys.argv[sys.argv.index("--vault") + 1])
    if "--channel" in sys.argv:
        channel = sys.argv[sys.argv.index("--channel") + 1]
    if "--raw-path" in sys.argv:
        raw_sub = sys.argv[sys.argv.index("--raw-path") + 1]

    raw_dir = os.path.join(vault, raw_sub)
    if not os.path.isdir(raw_dir):
        print("channel: {}".format(channel))
        print("  staged: 0 artifacts")
        print("  status: empty — drop files at {}/".format(raw_sub))
        return 0

    files = sorted(f for f in os.listdir(raw_dir) if os.path.isfile(os.path.join(raw_dir, f)))
    print("channel: {}".format(channel))
    print("  staged: {} artifact(s)".format(len(files)))
    for f in files:
        print("    · {}".format(f))
    print("  → run: python3 builder/map_channel.py --vault {} --channel {}".format(vault, channel))
    print("  → chart entries: builder/entries/  ·  templates: builder/templates/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
