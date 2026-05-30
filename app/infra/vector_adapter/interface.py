from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class VectorStoreAdapter(ABC):
    """Abstract interface for vector database operations.

    Used by: MemoryCenterService for semantic character name matching,
             semantic world-setting search, and context retrieval.

    Implementations: StubVectorStoreAdapter (default), future Qdrant/Chroma.
    """

    @abstractmethod
    def insert(
        self,
        collection: str,
        id: str,
        text: str,
        metadata: dict | None = None,
    ) -> None:
        """Insert a text embedding into a named collection."""
        ...

    @abstractmethod
    def search(
        self,
        collection: str,
        query: str,
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[dict]:
        """Search for top_k nearest neighbors.

        Returns list of {"id": str, "text": str, "score": float, "metadata": dict}
        """
        ...

    @abstractmethod
    def delete(self, collection: str, id: str) -> None:
        """Delete an entry from a collection."""
        ...

    @abstractmethod
    def delete_collection(self, collection: str) -> None:
        """Delete an entire collection."""
        ...


class StubVectorStoreAdapter(VectorStoreAdapter):
    """Stub implementation that always returns empty results.

    Logs a warning on each call so developers know the vector store is not configured.
    Designed to be a drop-in placeholder — no crashes, no side effects.
    """

    def insert(
        self,
        collection: str,
        id: str,
        text: str,
        metadata: dict | None = None,
    ) -> None:
        logger.debug(
            'Vector store stub: insert collection=%s id=%s (ignored)',
            collection,
            id,
        )

    def search(
        self,
        collection: str,
        query: str,
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[dict]:
        logger.debug(
            'Vector store stub: search collection=%s top_k=%d (returned empty)',
            collection,
            top_k,
        )
        return []

    def delete(self, collection: str, id: str) -> None:
        logger.debug(
            'Vector store stub: delete collection=%s id=%s (ignored)',
            collection,
            id,
        )

    def delete_collection(self, collection: str) -> None:
        logger.debug(
            'Vector store stub: delete_collection=%s (ignored)',
            collection,
        )
