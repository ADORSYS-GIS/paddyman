"""Abstract base and data types for embedding provider clients.

All provider implementations must satisfy the :class:`BaseEmbeddingClient`
interface so that the embedding pipeline is provider-agnostic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EmbeddingRequest:
    """Typed input for one embedding call."""

    text: str
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingResponse:
    """Normalised output from one embedding call."""

    vector: list[float]
    model: str
    provider: str

    @property
    def dimension(self) -> int:
        """Return the length of the embedding vector."""
        return len(self.vector)


class EmbeddingClientError(Exception):
    """Raised on non-retryable errors from the embedding provider."""


class BaseEmbeddingClient(ABC):
    """Provider-agnostic interface for text embedding.

    To add a new provider, implement :meth:`embed`, :meth:`embed_batch`,
    :attr:`model`, and :attr:`provider_name`.  No other file needs to change.
    """

    @property
    @abstractmethod
    def model(self) -> str:
        """Return the model identifier in use."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return a short, stable provider identifier (e.g. ``"openai_compat"``)."""

    @abstractmethod
    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Embed a single text and return the normalised response.

        Raises:
            EmbeddingClientError: on unrecoverable provider errors.
        """

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[EmbeddingResponse]:
        """Embed multiple texts in a single provider call.

        Raises:
            EmbeddingClientError: on unrecoverable provider errors.
        """
