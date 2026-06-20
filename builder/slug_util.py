#!/usr/bin/env python3
"""Shared slug normalization for themes and wiki links."""

import re

_THEME_STOPWORDS = frozenset({"a", "an", "the", "and", "of", "or", "in", "on", "for"})


def canonical_slug(name):
    """Lowercase kebab-case slug — the canonical identity for themes and wiki targets."""
    if not name:
        return ""
    base = str(name).strip().lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return base


def pick_preferred_slug(candidates, theme_meta=None):
    """Choose one slug when several normalize to the same canonical form."""
    if not candidates:
        return ""
    if len(candidates) == 1:
        return candidates[0]

    theme_meta = theme_meta or {}

    def score(slug):
        canon = canonical_slug(slug)
        exact = 1 if slug == canon else 0
        in_themes = 1 if slug in theme_meta else 0
        canon_in_themes = 1 if canon in theme_meta else 0
        has_note = 1 if theme_meta.get(slug, (None, None, False))[2] else 0
        return (canon_in_themes, in_themes, has_note, exact, -len(slug))

    return max(candidates, key=score)


def merge_theme_slugs(slugs, theme_meta=None):
    """Map raw theme slugs to a single canonical slug per identity."""
    theme_meta = theme_meta or {}
    groups = {}
    for slug in slugs:
        if not slug:
            continue
        canon = canonical_slug(slug)
        if not canon:
            continue
        groups.setdefault(canon, []).append(slug)

    aliases = {}
    canonical = {}
    for canon, variants in groups.items():
        preferred = pick_preferred_slug(variants, theme_meta)
        canonical[canon] = preferred
        for variant in variants:
            aliases[variant] = preferred
        aliases[preferred] = preferred
    return aliases, canonical


def dedupe_themes(themes_dict):
    """Merge THEMES entries that differ only by slug casing/format.

    Returns (merged_themes, slug_aliases) where slug_aliases maps any variant to the kept slug.
    """
    if not themes_dict:
        return {}, {}

    groups = {}
    for slug, meta in themes_dict.items():
        canon = canonical_slug(slug)
        if not canon:
            continue
        groups.setdefault(canon, []).append((slug, meta))

    merged = {}
    aliases = {}
    for canon, items in groups.items():
        slugs = [s for s, _ in items]
        preferred = pick_preferred_slug(slugs, {s: m for s, m in items})
        # Prefer the display name from the entry with a source note, else longest title.
        def title_score(item):
            slug, meta = item
            name, _core, has_note = meta
            return (1 if has_note else 0, len(name or ""), slug == preferred)

        _slug, meta = max(items, key=title_score)
        name, core, has_note = meta
        # If preferred slug's meta exists, use that tuple but keep best title.
        pref_meta = next((m for s, m in items if s == preferred), meta)
        best_name = name or pref_meta[0]
        merged[preferred] = (best_name, core or pref_meta[1], has_note or pref_meta[2])
        for slug, _ in items:
            aliases[slug] = preferred
            aliases[preferred] = preferred
    return merged, aliases


def normalize_theme_label(text):
    """Compare theme display names independent of punctuation and casing."""
    if not text:
        return ""
    s = str(text).lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def theme_identity(slug):
    """Token identity for themes — ignores stopwords like 'and'."""
    base = canonical_slug(slug)
    if not base:
        return ""
    tokens = [t for t in base.split("-") if t and t not in _THEME_STOPWORDS]
    return "-".join(sorted(tokens)) if tokens else base


def build_theme_resolver(themes_dict):
    """Resolve variant theme slugs to the canonical slug registered in THEMES.

    Returns (resolve, merged_themes, slug_aliases).
    """
    merged, aliases = dedupe_themes(themes_dict)
    by_identity = {}
    by_label = {}
    for slug, meta in merged.items():
        name = meta[0]
        ident = theme_identity(slug)
        label = normalize_theme_label(name)
        if ident:
            by_identity[ident] = slug
        if label:
            by_label[label] = slug

    def resolve(slug, display_hint=None):
        if not slug:
            return slug
        raw = str(slug).strip()
        s = canonical_slug(raw)
        if s in merged:
            return s
        if raw in aliases:
            return aliases[raw]
        if s in aliases:
            return aliases[s]
        ident = theme_identity(s)
        if ident in by_identity:
            return by_identity[ident]
        for hint in (display_hint, s.replace("-", " ")):
            if not hint:
                continue
            label = normalize_theme_label(hint)
            if label in by_label:
                return by_label[label]
        return s

    return resolve, merged, aliases
