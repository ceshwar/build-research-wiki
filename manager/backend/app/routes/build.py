from fastapi import APIRouter, HTTPException

from app.models.schemas import BuildResponse
from app.services.build_service import BuildService
from app.deps import vault_manager

router = APIRouter(prefix="/build", tags=["build"])
build_service = BuildService(vault_manager)


@router.post("/wiki", response_model=BuildResponse)
def rebuild_wiki(vault_id: str, mode: str = "auto"):
    if mode not in ("auto", "incremental", "full"):
        raise HTTPException(status_code=400, detail="mode must be auto, incremental, or full")
    try:
        job_id = build_service.rebuild_wiki(vault_id, mode=mode)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Vault '{vault_id}' not found")
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return BuildResponse(job_id=job_id, mode=mode)


@router.post("/extract", response_model=BuildResponse)
def extract_pdfs(vault_id: str):
    try:
        job_id = build_service.extract_pdfs(vault_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Vault '{vault_id}' not found")
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return BuildResponse(job_id=job_id, mode="extract")
