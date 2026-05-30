from __future__ import annotations

from app.infra.storage.adapter import StorageAdapter
from app.infra.storage.local import LocalStorageAdapter
from app.config.settings import settings

_storage: StorageAdapter | None = None


def get_storage() -> StorageAdapter:
    """Get the configured storage adapter singleton."""
    global _storage
    if _storage is None:
        _storage = LocalStorageAdapter(base_dir=settings.data_dir)
    return _storage


__all__ = ['get_storage', 'StorageAdapter', 'LocalStorageAdapter']
