from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import UploadResponse
from app.services.channel_registry import channel_registry
from app.services.vault_manager import VaultManager

router = APIRouter(tags=["dock"])
vault_manager = VaultManager()


@router.post("/dock", response_model=UploadResponse)
@router.post("/airlock", response_model=UploadResponse)
@router.post("/upload", response_model=UploadResponse)
async def dock(
    vault_id: str,
    files: List[UploadFile] = File(...),
    channel_id: str = "my-portfolio",
    artifact_type: str = "",
):
    """Stage artifacts into the channel's raw/ folder. No chart update."""
    ch = channel_registry.get(channel_id)
    if not ch:
        raise HTTPException(status_code=400, detail="Unknown channel '{}'".format(channel_id))

    try:
        dest_dir = vault_manager.ensure_channel_dir(vault_id, channel_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Vault '{}' not found".format(vault_id))

    saved = []  # type: List[str]
    for f in files:
        if not f.filename:
            continue
        dest = dest_dir / f.filename
        content = await f.read()
        dest.write_bytes(content)
        saved.append(f.filename)

    return UploadResponse(
        files_added=len(saved),
        filenames=saved,
        channel_id=channel_id,
        channel_name=ch["name"],
        raw_path=ch["raw_path"],
    )
