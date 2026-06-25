"""Read vault files for in-app viewer."""

import os
from pathlib import Path

from fastapi import HTTPException


def resolve_vault_file(vault_path, rel_path):
    """Return absolute path if rel_path is inside vault and exists."""
    vault_path = Path(vault_path).resolve()
    rel = rel_path.replace("\\", "/").lstrip("/")
    if ".." in rel.split("/"):
        raise HTTPException(status_code=400, detail="Invalid path")
    abs_path = (vault_path / rel).resolve()
    if not str(abs_path).startswith(str(vault_path)):
        raise HTTPException(status_code=400, detail="Path outside vault")
    if not abs_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return abs_path


def read_vault_file(vault_path, rel_path, max_bytes=512_000):
    abs_path = resolve_vault_file(vault_path, rel_path)
    if abs_path.suffix.lower() == ".pdf":
        return {
            "path": rel_path.replace("\\", "/"),
            "content_type": "application/pdf",
            "content": None,
            "size": abs_path.stat().st_size,
        }
    raw = abs_path.read_bytes()[:max_bytes]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")
    ctype = "text/markdown" if abs_path.suffix.lower() == ".md" else "text/plain"
    return {
        "path": rel_path.replace("\\", "/"),
        "content_type": ctype,
        "content": text,
        "size": abs_path.stat().st_size,
    }
