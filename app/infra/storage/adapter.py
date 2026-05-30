from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class StorageAdapter(ABC):
    """Abstract file-storage adapter.

    One implementation for local filesystem now.
    Extensible to S3/MinIO later.
    """

    @abstractmethod
    def write_text(self, relative_path: str, content: str, encoding: str = 'utf-8') -> Path:
        """Write text content to a relative path. Returns absolute path."""
        ...

    @abstractmethod
    def write_bytes(self, relative_path: str, content: bytes) -> Path:
        """Write bytes content to a relative path. Returns absolute path."""
        ...

    @abstractmethod
    def read_text(self, relative_path: str, encoding: str = 'utf-8') -> str:
        """Read text content from a relative path."""
        ...

    @abstractmethod
    def read_bytes(self, relative_path: str) -> bytes:
        """Read bytes content from a relative path."""
        ...

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Check if a file exists at the relative path."""
        ...

    @abstractmethod
    def delete(self, relative_path: str) -> None:
        """Delete a file at the relative path."""
        ...

    @abstractmethod
    def mkdirs(self, relative_path: str) -> Path:
        """Create directories recursively. Returns absolute path."""
        ...
