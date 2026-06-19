from typing import List

from fastapi import APIRouter, HTTPException

from app.models.schemas import BuildResponse, ChannelSummary
from app.services.channel_registry import channel_registry
from app.services.map_service import MapService
from app.services.vault_manager import VaultManager

router = APIRouter(tags=["surface"])
vault_manager = VaultManager()
map_service = MapService(vault_manager)


@router.get("/channels", response_model=List[ChannelSummary])
def list_channels():
    return [
        ChannelSummary(
            id=ch["id"],
            name=ch["name"],
            description=ch.get("description", ""),
            profile=ch["profile"],
            raw_path=ch["raw_path"],
            extensions=ch.get("extensions", []),
        )
        for ch in channel_registry.list_channels()
    ]


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
