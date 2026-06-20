from typing import List

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    VaultAddRequest,
    VaultPickFolderResponse,
    VaultSummary,
    VaultValidateRequest,
    VaultValidateResponse,
)
from app.deps import vault_manager

router = APIRouter(prefix="/vaults", tags=["vaults"])


@router.get("", response_model=List[VaultSummary])
def list_vaults():
    return vault_manager.list_vaults()


@router.post("/validate", response_model=VaultValidateResponse)
def validate_vault(body: VaultValidateRequest):
    result = vault_manager.validate_path(body.path)
    return VaultValidateResponse(**result)


@router.post("/pick-folder", response_model=VaultPickFolderResponse)
def pick_folder():
    path = vault_manager.pick_folder()
    if not path:
        return VaultPickFolderResponse(cancelled=True)
    return VaultPickFolderResponse(path=path, cancelled=False)


@router.post("", response_model=VaultSummary)
def add_vault(body: VaultAddRequest):
    try:
        return vault_manager.add_vault(body.path, body.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{vault_id}")
def remove_vault(vault_id: str):
    try:
        vault_manager.remove_vault(vault_id)
        return {"ok": True}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{vault_id}", response_model=VaultSummary)
def get_vault(vault_id: str):
    try:
        return vault_manager.get_vault(vault_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Vault '{}' not found".format(vault_id))
