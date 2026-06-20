"""Shared service instances — one VaultManager per process."""

from app.services.vault_manager import VaultManager

vault_manager = VaultManager()
