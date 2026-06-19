"""Load and fill SCUBA entry templates."""

import os

BUILDER_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BUILDER_DIR, "templates")


def template_path(channel_id, kind="entry"):
    name = "entry.md" if kind == "entry" else "deepdive.md"
    path = os.path.join(TEMPLATES_DIR, channel_id, name)
    if os.path.exists(path):
        return path
    fallback = "my-portfolio" if kind == "entry" else "my-portfolio"
    return os.path.join(TEMPLATES_DIR, fallback, name)


def fill_template(channel_id, kind="entry", **kwargs):
    with open(template_path(channel_id, kind)) as f:
        text = f.read()
    for key, val in kwargs.items():
        text = text.replace("{" + key + "}", str(val))
    text = text.replace("{slug}", kwargs.get("slug", ""))
    return text


def entry_rel_path(channel_id, slug):
    return "builder/entries/{}/{}.md".format(channel_id, slug)


def deepdive_rel_path(slug):
    return "builder/deepdives/{}.md".format(slug)
