from fastapi import APIRouter, HTTPException

from app.models.schemas import AppSettingsResponse, AppSettingsUpdateRequest, VaultFileResponse
from app.services.settings_service import save_settings, settings_for_api

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=AppSettingsResponse)
def get_settings():
    return AppSettingsResponse(**settings_for_api())


@router.patch("", response_model=AppSettingsResponse)
def patch_settings(body: AppSettingsUpdateRequest):
    patch = body.model_dump(exclude_unset=True)
    updated = save_settings(patch)
    return AppSettingsResponse(**settings_for_api())
