from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.models.schemas import BuildResponse, ChannelSummary, DockCreateRequest
from app.services.channel_registry import channel_registry
from app.services.map_service import MapService
from app.services.vault_manager import VaultManager

router = APIRouter(tags=["surface"])
vault_manager = VaultManager()
map_service = MapService(vault_manager)


@router.get("/channels", response_model=List[ChannelSummary])
def list_channels(vault_id: Optional[str] = None, include_hidden: bool = False):
    vault_path = None
    if vault_id:
        try:
            vault_path = vault_manager.resolve_path(vault_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Vault not found")
    return [
        ChannelSummary(**ch)
        for ch in channel_registry.list_channels(vault_path, include_hidden=include_hidden)
    ]


@router.post("/vaults/{vault_id}/docks", response_model=ChannelSummary)
def create_dock(vault_id: str, body: DockCreateRequest):
    try:
        vault_path = vault_manager.resolve_path(vault_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Vault not found")
    dock = channel_registry.create_dock(
        vault_path,
        name=body.name,
        emoji=body.emoji,
        description=body.description,
        profile=body.profile,
    )
    return ChannelSummary(**dock)


@router.post("/update-map", response_model=BuildResponse)
@router.post("/surface_interval", response_model=BuildResponse)
def surface_interval(vault_id: str, channel_id: str = "my-portfolio", mode: str = "auto"):
    if mode not in ("auto", "incremental", "full"):
        raise HTTPException(status_code=400, detail="mode must be auto, incremental, or full")
    try:
        job_id = map_service.surface_interval(vault_id, channel_id=channel_id, build_mode=mode)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return BuildResponse(job_id=job_id, mode="surface_interval", channel_id=channel_id)


@router.post("/map", response_model=BuildResponse)
def map_only(vault_id: str, channel_id: str = "my-portfolio"):
    try:
        job_id = map_service.map_pdfs(vault_id, channel_id=channel_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return BuildResponse(job_id=job_id, mode="map", channel_id=channel_id)
