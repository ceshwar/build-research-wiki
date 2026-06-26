from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.models.schemas import UploadResponse
from app.services.channel_registry import channel_registry
from app.deps import vault_manager

router = APIRouter(tags=["dock"])


class DuplicateMatch(BaseModel):
    slug: str
    title: str
    match_type: str
    pdf_path: str = ""


class PreflightFileResult(BaseModel):
    filename: str
    matches: List[DuplicateMatch]
    preprint: bool = False
    arxiv_id: str = ""


class DockPreflightResponse(BaseModel):
    files: List[PreflightFileResult]


@router.post("/dock/preflight", response_model=DockPreflightResponse)
async def dock_preflight(
    vault_id: str,
    files: List[UploadFile] = File(...),
    channel_id: str = "my-portfolio",
):
    try:
        vault_path = vault_manager.resolve_path(vault_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Vault '{}' not found".format(vault_id))
    ch = channel_registry.get(channel_id, vault_path)
    if not ch:
        raise HTTPException(status_code=400, detail="Unknown channel '{}'".format(channel_id))

    import sys
    from pathlib import Path
    repo = Path(__file__).resolve().parents[4]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from builder import dock_duplicates

    results = []
    import tempfile
    import os

    for f in files:
        if not f.filename:
            continue
        content = await f.read()
        suffix = os.path.splitext(f.filename)[1] or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            extracted = dock_duplicates.extract_for_duplicate_check(tmp_path)
            matches = dock_duplicates.find_duplicate_matches(
                str(vault_path), channel_id, f.filename, extracted)
            results.append(PreflightFileResult(
                filename=f.filename,
                matches=[DuplicateMatch(**m) for m in matches],
                preprint=bool(extracted.get("preprint")),
                arxiv_id=extracted.get("arxiv_id") or "",
            ))
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    return DockPreflightResponse(files=results)


@router.post("/dock", response_model=UploadResponse)
@router.post("/airlock", response_model=UploadResponse)
@router.post("/upload", response_model=UploadResponse)
async def dock(
    vault_id: str,
    files: List[UploadFile] = File(...),
    channel_id: str = "my-portfolio",
    artifact_type: str = "",
    policies_json: str = Form(""),
):
    """Stage artifacts into the channel's raw/ folder. No chart update."""
    try:
        vault_path = vault_manager.resolve_path(vault_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Vault '{}' not found".format(vault_id))
    ch = channel_registry.get(channel_id, vault_path)
    if not ch:
        raise HTTPException(status_code=400, detail="Unknown channel '{}'".format(channel_id))

    try:
        dest_dir = vault_manager.ensure_channel_dir(vault_id, channel_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Vault '{}' not found".format(vault_id))

    policies = {}
    if policies_json.strip():
        import json
        try:
            for row in json.loads(policies_json):
                policies[row.get("filename")] = row
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid policies_json")

    import sys
    from pathlib import Path
    repo = Path(__file__).resolve().parents[4]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from builder import dock_duplicates

    raw_path = ch["raw_path"]
    saved = []  # type: List[str]
    for f in files:
        if not f.filename:
            continue
        policy = policies.get(f.filename) or {}
        action = policy.get("action", "upload")
        if action == "skip":
            continue

        content = await f.read()
        dest = dest_dir / f.filename
        dest.write_bytes(content)
        rel_pdf = "{}/{}".format(raw_path, f.filename).replace("\\", "/")

        if action == "merge" and policy.get("merge_into_slug"):
            import tempfile
            import os
            suffix = os.path.splitext(f.filename)[1] or ".pdf"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            try:
                extracted = dock_duplicates.extract_for_duplicate_check(tmp_path)
                dock_duplicates.apply_merge_to_entry(
                    str(vault_path),
                    channel_id,
                    policy["merge_into_slug"],
                    extracted,
                    policy.get("merge_fields") or {},
                    rel_pdf if (policy.get("merge_fields") or {}).get("pdf") == "new" else "",
                )
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
        saved.append(f.filename)

    return UploadResponse(
        files_added=len(saved),
        filenames=saved,
        channel_id=channel_id,
        channel_name=ch["name"],
        raw_path=ch["raw_path"],
    )
