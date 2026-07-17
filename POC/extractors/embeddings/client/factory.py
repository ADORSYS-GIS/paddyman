"""Embedding client factory — creates a client from ``shared.config.settings``.

Changing the provider, base URL, model, or credentials requires only central
configuration updates; no code changes are needed.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure POC/ is importable (file: POC/3_Extractors/embeddings/client/factory.py).
_poc_root = str(Path(__file__).resolve().parents[3])
if _poc_root not in sys.path:
    sys.path.insert(0, _poc_root)

from .base_client import BaseEmbeddingClient


def create_client() -> BaseEmbeddingClient:
    """Return an embedding client configured from ``shared.config.settings``.

    Configuration keys read through ``shared.config``:

    - ``EMBED_BASE_URL``    — provider base URL (required)
    - ``EMBED_MODEL_NAME``  — model identifier
    - ``EMBED_API_KEY``     — authentication key (required)
    - ``EMBED_TIMEOUT``     — per-request timeout in seconds

    Raises:
        ConfigurationError: when required configuration is absent.

    Returns:
        A configured :class:`~client.base_client.BaseEmbeddingClient`.
    """
    from shared.config import settings
    from shared.config.loader import ConfigurationError
    from .openai_compat_client import OpenAICompatEmbeddingClient

    if not settings.embed_base_url:
        raise ConfigurationError(
            "Embedding base URL is required. Add embedding.base_url to POC/config.yml — "
            "see POC/config.yml for application config."
        )
    if not settings.embed_api_key:
        raise ConfigurationError(
            "EMBED_API_KEY is required. Add it to POC/.env — "
            "see POC/.env.example for secrets."
        )

    return OpenAICompatEmbeddingClient(
        base_url=settings.embed_base_url,
        api_key=settings.embed_api_key,
        model=settings.embed_model_name,
        timeout=settings.embed_timeout,
    )
