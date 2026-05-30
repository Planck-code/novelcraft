from __future__ import annotations

from pathlib import Path

from app.infra.storage.adapter import StorageAdapter


class LocalStorageAdapter(StorageAdapter):
    """Local filesystem implementation of StorageAdapter."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir.resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, relative_path: str) -> Path:
        # Prevent directory traversal
        resolved = (self.base_dir / relative_path).resolve()
        if not str(resolved).startswith(str(self.base_dir)):
            raise ValueError(f'Path traversal detected: {relative_path}')
        return resolved

    def write_text(self, relative_path: str, content: str, encoding: str = 'utf-8') -> Path:
        path = self._resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)
        return path

    def write_bytes(self, relative_path: str, content: bytes) -> Path:
        path = self._resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def read_text(self, relative_path: str, encoding: str = 'utf-8') -> str:
        path = self._resolve(relative_path)
        return path.read_text(encoding=encoding)

    def read_bytes(self, relative_path: str) -> bytes:
        path = self._resolve(relative_path)
        return path.read_bytes()

    def exists(self, relative_path: str) -> bool:
        return self._resolve(relative_path).exists()

    def delete(self, relative_path: str) -> None:
        path = self._resolve(relative_path)
        if path.exists():
            path.unlink()

    def mkdirs(self, relative_path: str) -> Path:
        path = self._resolve(relative_path)
        path.mkdir(parents=True, exist_ok=True)
        return path
