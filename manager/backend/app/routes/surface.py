import os
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    BuildResponse,
    ChannelSummary,
    ChartMapResponse,
    DockCreateRequest,
    IngestPromptResponse,
    RemoveFromChartResponse,
    RemoveFromChartBatchRequest,
    RemoveFromChartBatchResponse,
)
from app.services.channel_registry import channel_registry
from app.services.map_service import MapService
from app.deps import vault_manager

router = APIRouter(tags=["surface"])
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


@router.get("/ingest-prompt", response_model=IngestPromptResponse)
def ingest_prompt(vault_id: str, channel_id: str = "my-portfolio"):
    """Paste-ready prompt for the user's own coding agent (manual-agent ingest)."""
    try:
        vault_path = vault_manager.resolve_path(vault_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Vault not found")
    import ingest_prompt as ip  # builder/ is on sys.path (via channel_registry import)
    text, count = ip.build_prompt(str(vault_path), channel_id)
    return IngestPromptResponse(prompt=text, count=count, channel_id=channel_id)


@router.get("/chart-map", response_model=ChartMapResponse)
def chart_map(vault_id: str, channel_id: str = "my-portfolio"):
    """Papers on chart + raw dock files for portfolio / channel map UI."""
    try:
        vault_path = vault_manager.resolve_path(vault_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Vault not found")
    import chart_map as cm
    data = cm.build_map(str(vault_path), channel_id)
    return ChartMapResponse(**data)


@router.delete("/chart-entry", response_model=RemoveFromChartResponse)
def remove_chart_entry(vault_id: str, channel_id: str, slug: str):
    """Remove a paper from the chart; PDF stays in raw/ as awaiting chart."""
    try:
        result, job_id = map_service.remove_from_chart(vault_id, channel_id, slug)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return RemoveFromChartResponse(
        slug=result["slug"],
        channel_id=result["channel_id"],
        deleted_files=[os.path.basename(p) for p in result.get("deleted", [])],
        job_id=job_id,
    )


@router.post("/chart-remove", response_model=RemoveFromChartBatchResponse)
def remove_chart_entries_batch(
    vault_id: str,
    channel_id: str,
    body: RemoveFromChartBatchRequest,
):
    """Remove multiple papers from the chart; one rebuild at the end."""
    if not body.slugs:
        raise HTTPException(status_code=400, detail="No slugs provided.")
    try:
        removed, job_id = map_service.remove_many_from_chart(vault_id, channel_id, body.slugs)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return RemoveFromChartBatchResponse(
        channel_id=channel_id,
        removed=removed,
        job_id=job_id,
    )


@router.post("/map", response_model=BuildResponse)
def map_only(vault_id: str, channel_id: str = "my-portfolio"):
    try:
        job_id = map_service.map_pdfs(vault_id, channel_id=channel_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return BuildResponse(job_id=job_id, mode="map", channel_id=channel_id)
