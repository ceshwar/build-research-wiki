from typing import List

from fastapi import APIRouter, HTTPException

from app.models.schemas import VaultSummary
from app.services.vault_manager import VaultManager

router = APIRouter(prefix="/vaults", tags=["vaults"])
vault_manager = VaultManager()


@router.get("", response_model=List[VaultSummary])
def list_vaults():
    return vault_manager.list_vaults()


@router.get("/{vault_id}", response_model=VaultSummary)
def get_vault(vault_id: str):
    try:
        return vault_manager.get_vault(vault_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Vault '{vault_id}' not found")
