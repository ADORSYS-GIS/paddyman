"""OpenAI-compatible embedding client.

Covers any provider that exposes an OpenAI-compatible ``/embeddings`` endpoint:
Qwen, OpenAI, Azure OpenAI, Ollama, Jina AI, Voyage AI, Nomic, Gemini (via proxy).
Switch providers by changing ``EMBED_BASE_URL``, ``EMBED_MODEL_NAME``, and
``EMBED_API_KEY`` — no code changes required.
"""
from __future__ import annotations

import logging
from typing import Any

from .base_client import (
    BaseEmbeddingClient,
    EmbeddingClientError,
    EmbeddingRequest,
    EmbeddingResponse,
)

logger = logging.getLogger(__name__)

_PROVIDER_NAME = "openai_compat"


class OpenAICompatEmbeddingClient(BaseEmbeddingClient):
    """Embedding client backed by the ``openai`` Python SDK.

    Compatible providers (configure via env — no code changes):

    - **Qwen** — ``https://api.ai.camer.digital/v1``
    - **OpenAI** — ``https://api.openai.com/v1``
    - **Azure OpenAI** — ``https://<resource>.openai.azure.com/...``
    - **Ollama** — ``http://localhost:11434/v1``
    - **Jina AI**, **Voyage AI**, **Nomic** — point to their base URLs

    Args:
        base_url: Provider base URL.
        api_key:  Authentication key.
        model:    Embedding model identifier.
        timeout:  Per-request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int = 60,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError(
                "openai>=1.0.0 is required. Run: pip install openai>=1.0.0"
            ) from exc

        self._model = model
        self._sdk = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)
        logger.debug(
            "OpenAICompatEmbeddingClient ready: model=%s base=%s", model, base_url
        )

    @property
    def model(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return _PROVIDER_NAME

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Embed a single text via the provider.

        Raises:
            EmbeddingClientError: on provider errors.
        """
        try:
            resp = self._sdk.embeddings.create(
                model=self._model,
                input=request.text,
                **self._extra_kwargs(request.extra),
            )
        except Exception as exc:
            raise EmbeddingClientError(f"Embedding failed: {exc}") from exc

        vector: list[float] = resp.data[0].embedding
        return EmbeddingResponse(
            vector=vector,
            model=resp.model,
            provider=_PROVIDER_NAME,
        )

    def embed_batch(self, texts: list[str]) -> list[EmbeddingResponse]:
        """Embed multiple texts in one provider call.

        Raises:
            EmbeddingClientError: on provider errors.
        """
        if not texts:
            return []
        try:
            resp = self._sdk.embeddings.create(
                model=self._model,
                input=texts,
            )
        except Exception as exc:
            raise EmbeddingClientError(f"Batch embedding failed: {exc}") from exc

        resp.data.sort(key=lambda d: d.index)
        return [
            EmbeddingResponse(
                vector=item.embedding,
                model=resp.model,
                provider=_PROVIDER_NAME,
            )
            for item in resp.data
        ]

    @staticmethod
    def _extra_kwargs(extra: dict[str, Any]) -> dict[str, Any]:
        """Filter and pass-through supported optional SDK kwargs."""
        allowed = {"dimensions", "encoding_format", "user"}
        return {k: v for k, v in extra.items() if k in allowed}
