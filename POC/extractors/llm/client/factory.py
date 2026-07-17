"""LLM client factory — creates a client from ``shared.config.settings``.

Changing the provider, base URL, model, or credentials requires only central
configuration updates; no code changes are needed.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure POC/ is importable (file: POC/3_Extractors/llm/client/factory.py).
_poc_root = str(Path(__file__).resolve().parents[3])
if _poc_root not in sys.path:
    sys.path.insert(0, _poc_root)

from .base_client import BaseLLMClient


def create_client() -> BaseLLMClient:
    """Return an LLM client configured from ``shared.config.settings``.

    Configuration keys read through ``shared.config``:

    - ``LLM_BASE_URL``    — provider base URL
    - ``LLM_MODEL``       — model identifier
    - ``LLM_API_KEY``     — authentication key (required)
    - ``LLM_TIMEOUT``     — per-request timeout in seconds

    Raises:
        ConfigurationError: when ``LLM_API_KEY`` is not set.

    Returns:
        A configured :class:`~client.base_client.BaseLLMClient` instance.
    """
    from shared.config import settings
    from shared.config.loader import ConfigurationError
    from client.openai_compat_client import OpenAICompatClient

    if not settings.llm_api_key:
        raise ConfigurationError(
            "LLM_API_KEY is required. Add it to POC/.env — "
            "see POC/.env.example for secrets and POC/config.yml for app config."
        )

    return OpenAICompatClient(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        timeout=settings.llm_timeout,
    )
