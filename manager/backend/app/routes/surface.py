import os
from typing import List, Optional

from fastapi import APIRouter, Body, HTTPException

from app.models.schemas import (
    BuildResponse,
    ChannelSummary,
    ChartGraphResponse,
    ChartMapResponse,
    DeepDiveRequest,
    DeepDiveResponse,
    DockCreateRequest,
    IngestPromptResponse,
    LlmConfigResponse,
    QueryRequest,
    QueryResponse,
    QueryResultResponse,
    RemoveFromChartResponse,
    RemoveFromChartBatchRequest,
    RemoveFromChartBatchResponse,
    VaultFileResponse,
    VerificationUpdateRequest,
    VerificationUpdateResponse,
)
from app.services.channel_registry import channel_registry
from app.services.deep_dive_service import DeepDiveService
from app.services.map_service import MapService
from app.services.query_service import QueryService
from app.services.settings_service import settings_for_api
from app.services.vault_files import read_vault_file
from app.deps import vault_manager

router = APIRouter(tags=["surface"])
map_service = MapService(vault_manager)
deep_dive_service = DeepDiveService(vault_manager)
query_service = QueryService(vault_manager)


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


@router.get("/llm-config", response_model=LlmConfigResponse)
def llm_config():
    """LLM defaults (mirrors Settings)."""
    s = settings_for_api()
    llm = s["llm"]
    models = llm["models"]
    return LlmConfigResponse(
        ollama_url=llm["ollama_url"],
        default_model=models["deep_dive"],
        embedding_model="nomic-embed-text:latest",
        think=llm.get("think", False),
        stages=models,
    )


@router.get("/vault-file", response_model=VaultFileResponse)
def vault_file(vault_id: str, path: str):
    """Read a markdown/text file from the vault for in-app viewer."""
    try:
        vault_path = vault_manager.resolve_path(vault_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Vault not found")
    data = read_vault_file(str(vault_path), path)
    return VaultFileResponse(**data)


@router.post("/deep-dive", response_model=DeepDiveResponse)
def run_deep_dive(
    vault_id: str,
    channel_id: str = "my-portfolio",
    body: DeepDiveRequest = Body(default_factory=DeepDiveRequest),
):
    slugs = list(body.slugs or [])
    if body.slug:
        slugs = [body.slug]
    if not slugs:
        raise HTTPException(status_code=400, detail="Provide slug or slugs")
    try:
        if len(slugs) == 1:
            job_id, model, provider = deep_dive_service.run_deep_dive(
                vault_id, channel_id, slugs[0], body.provider, body.model)
        else:
            job_id, model, provider = deep_dive_service.run_deep_dive_batch(
                vault_id, channel_id, slugs, body.provider, body.model)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return DeepDiveResponse(job_id=job_id, model=model, provider=provider, slugs=slugs)


@router.post("/query", response_model=QueryResponse)
def run_query(vault_id: str, body: QueryRequest):
    """Ask a question against the wiki (async job)."""
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question required")
    try:
        job_id, model, provider = query_service.run_query(
            vault_id, body.question.strip(), body.provider, body.model, body.scope)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return QueryResponse(
        job_id=job_id, model=model, provider=provider, question=body.question.strip())


@router.get("/query/{job_id}", response_model=QueryResultResponse)
def query_result(job_id: str, question: str = ""):
    from app.services.process_manager import process_manager
    job = process_manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    result = query_service.read_query_result(job_id)
    return QueryResultResponse(
        job_id=job_id,
        status=job.get("status", "unknown"),
        question=question or (result or {}).get("question", ""),
        answer=(result or {}).get("answer", ""),
        model=(result or {}).get("model", ""),
        elapsed_s=(result or {}).get("elapsed_s"),
        provider_kind=(result or {}).get("provider_kind", ""),
    )


@router.post("/chart-entry/verification", response_model=VerificationUpdateResponse)
def update_chart_verification(
    vault_id: str,
    channel_id: str,
    slug: str,
    body: VerificationUpdateRequest,
):
    """Mark a processed paper human-verified (or revoke). Rebuilds wiki frontmatter."""
    try:
        rec, job_id = map_service.set_verification(
            vault_id,
            channel_id,
            slug,
            body.human_verified,
            verified_by=body.verified_by,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return VerificationUpdateResponse(
        slug=slug,
        channel_id=channel_id,
        human_verified=bool(rec.get("human_verified", body.human_verified)),
        verified_at=rec.get("verified_at") or "",
        verified_by=rec.get("verified_by") or "",
        job_id=job_id,
    )


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


@router.get("/chart-graph", response_model=ChartGraphResponse)
def chart_graph(vault_id: str, channel_id: str = "my-portfolio"):
    """Wikilink graph for charted papers on a portfolio dock."""
    try:
        vault_path = vault_manager.resolve_path(vault_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Vault not found")
    import chart_graph as cg
    data = cg.build_graph(str(vault_path), channel_id)
    return ChartGraphResponse(**data)


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
