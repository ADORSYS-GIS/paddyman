"""Embedding client package."""
from .base_client import (
    BaseEmbeddingClient,
    EmbeddingClientError,
    EmbeddingRequest,
    EmbeddingResponse,
)

__all__ = [
    "BaseEmbeddingClient",
    "EmbeddingClientError",
    "EmbeddingRequest",
    "EmbeddingResponse",
]
