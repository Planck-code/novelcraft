from __future__ import annotations

from app.infra.vector_adapter.interface import StubVectorStoreAdapter, VectorStoreAdapter

_vector_store: VectorStoreAdapter | None = None


def get_vector_store() -> VectorStoreAdapter:
    """Factory that returns the configured vector store adapter.

    Currently always returns StubVectorStoreAdapter.
    Future: reads VECTOR_STORE_URL env var, returns QdrantAdapter or similar.
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = StubVectorStoreAdapter()
    return _vector_store
