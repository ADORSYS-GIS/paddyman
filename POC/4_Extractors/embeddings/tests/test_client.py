"""Tests for the embedding client layer (base types, OpenAI-compat, factory)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from client.base_client import (
    BaseEmbeddingClient,
    EmbeddingClientError,
    EmbeddingRequest,
    EmbeddingResponse,
)
from client.openai_compat_client import OpenAICompatEmbeddingClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_sdk_embed(vector: list[float] = None, model: str = "qwen3-embedding-8b"):
    if vector is None:
        vector = [0.1, 0.2, 0.3, 0.4]
    item = MagicMock()
    item.embedding = vector
    item.index = 0
    resp = MagicMock()
    resp.data = [item]
    resp.model = model
    return resp


def _mock_sdk_batch(vectors: list[list[float]], model: str = "qwen3-embedding-8b"):
    items = []
    for i, v in enumerate(vectors):
        item = MagicMock()
        item.embedding = v
        item.index = i
        items.append(item)
    resp = MagicMock()
    resp.data = items
    resp.model = model
    return resp


# ---------------------------------------------------------------------------
# BaseEmbeddingClient
# ---------------------------------------------------------------------------

class TestBaseEmbeddingClientIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseEmbeddingClient()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# EmbeddingRequest / EmbeddingResponse
# ---------------------------------------------------------------------------

class TestEmbeddingDataClasses:
    def test_request_is_frozen(self) -> None:
        req = EmbeddingRequest(text="hello")
        with pytest.raises((AttributeError, TypeError)):
            req.text = "changed"  # type: ignore[misc]

    def test_response_dimension(self) -> None:
        resp = EmbeddingResponse(vector=[1.0, 2.0, 3.0], model="m", provider="p")
        assert resp.dimension == 3


# ---------------------------------------------------------------------------
# OpenAICompatEmbeddingClient
# ---------------------------------------------------------------------------

class TestOpenAICompatEmbeddingClient:
    def test_model_and_provider_properties(self) -> None:
        with patch("openai.OpenAI"):
            client = OpenAICompatEmbeddingClient(
                base_url="http://test", api_key="key", model="test-embed"
            )
        assert client.model == "test-embed"
        assert client.provider_name == "openai_compat"

    def test_embed_returns_response(self) -> None:
        sdk_resp = _mock_sdk_embed([0.5, 0.6])
        with patch("openai.OpenAI") as mock_cls:
            mock_sdk = MagicMock()
            mock_cls.return_value = mock_sdk
            mock_sdk.embeddings.create.return_value = sdk_resp
            client = OpenAICompatEmbeddingClient(
                base_url="http://test", api_key="key", model="m"
            )
            result = client.embed(EmbeddingRequest(text="payment service"))

        assert isinstance(result, EmbeddingResponse)
        assert result.vector == [0.5, 0.6]
        assert result.dimension == 2
        assert result.provider == "openai_compat"

    def test_embed_raises_on_sdk_error(self) -> None:
        with patch("openai.OpenAI") as mock_cls:
            mock_sdk = MagicMock()
            mock_cls.return_value = mock_sdk
            mock_sdk.embeddings.create.side_effect = RuntimeError("connection error")
            client = OpenAICompatEmbeddingClient(
                base_url="http://test", api_key="key", model="m"
            )
            with pytest.raises(EmbeddingClientError, match="connection error"):
                client.embed(EmbeddingRequest(text="fail"))

    def test_embed_batch_returns_ordered_responses(self) -> None:
        sdk_resp = _mock_sdk_batch([[0.1, 0.2], [0.3, 0.4]])
        with patch("openai.OpenAI") as mock_cls:
            mock_sdk = MagicMock()
            mock_cls.return_value = mock_sdk
            mock_sdk.embeddings.create.return_value = sdk_resp
            client = OpenAICompatEmbeddingClient(
                base_url="http://test", api_key="key", model="m"
            )
            results = client.embed_batch(["text a", "text b"])

        assert len(results) == 2
        assert results[0].vector == [0.1, 0.2]
        assert results[1].vector == [0.3, 0.4]

    def test_embed_batch_empty_input(self) -> None:
        with patch("openai.OpenAI"):
            client = OpenAICompatEmbeddingClient(
                base_url="http://test", api_key="key", model="m"
            )
        assert client.embed_batch([]) == []

    def test_embed_batch_raises_on_sdk_error(self) -> None:
        with patch("openai.OpenAI") as mock_cls:
            mock_sdk = MagicMock()
            mock_cls.return_value = mock_sdk
            mock_sdk.embeddings.create.side_effect = RuntimeError("timeout")
            client = OpenAICompatEmbeddingClient(
                base_url="http://test", api_key="key", model="m"
            )
            with pytest.raises(EmbeddingClientError, match="timeout"):
                client.embed_batch(["a", "b"])
