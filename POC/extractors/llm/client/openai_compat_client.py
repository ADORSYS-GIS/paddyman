"""OpenAI-compatible client — covers any OpenAI-compatible provider (OpenAI, Azure OpenAI, Ollama, GLM, etc.).

Any provider that exposes an OpenAI-compatible ``chat/completions`` endpoint
works by adjusting ``base_url``, ``api_key``, and ``model`` via config.
"""
from __future__ import annotations

import logging
from typing import Any

from .base_client import (
    BaseLLMClient,
    CompletionRequest,
    CompletionResponse,
    LLMClientError,
)

logger = logging.getLogger(__name__)


class OpenAICompatClient(BaseLLMClient):
    """LLM client backed by the ``openai`` Python SDK.

    Compatible providers (configure via env vars — no code changes):

    - **Custom** — default: ``https://api.ai.camer.digital/v1`` (override via ``LLM_BASE_URL``)
    - **OpenAI** — ``https://api.openai.com/v1``
    - **Azure OpenAI** — ``https://<resource>.openai.azure.com/...``
    - **Ollama** — ``http://localhost:11434/v1``

    Args:
        base_url: Provider base URL.
        api_key:  Authentication key.
        model:    Model identifier string.
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
        logger.debug("OpenAICompatClient ready: model=%s base=%s", model, base_url)

    @property
    def model(self) -> str:
        return self._model

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        messages: list[dict[str, Any]] = [
            {"role": m.role, "content": m.content} for m in request.messages
        ]
        try:
            resp = self._sdk.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
        except Exception as exc:
            raise LLMClientError(f"Completion failed: {exc}") from exc

        content = resp.choices[0].message.content or ""
        usage: dict[str, int] = {}
        if resp.usage:
            usage = {
                "prompt_tokens": resp.usage.prompt_tokens or 0,
                "completion_tokens": resp.usage.completion_tokens or 0,
                "total_tokens": resp.usage.total_tokens or 0,
            }
        return CompletionResponse(content=content, model=resp.model, usage=usage)
