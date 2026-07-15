"""Tests for provider abstraction — verifying the interface contract."""
from __future__ import annotations

from abc import ABC
from unittest.mock import MagicMock, patch

import pytest

from client.base_client import (
    BaseEmbeddingClient,
    EmbeddingClientError,
    EmbeddingRequest,
    EmbeddingResponse,
)


class ConcreteClient(BaseEmbeddingClient):
    """Minimal concrete implementation for contract tests."""

    @property
    def model(self) -> str:
        return "test-model"

    @property
    def provider_name(self) -> str:
        return "test-provider"

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        return EmbeddingResponse(vector=[1.0], model=self.model, provider=self.provider_name)

    def embed_batch(self, texts: list[str]) -> list[EmbeddingResponse]:
        return [self.embed(EmbeddingRequest(text=t)) for t in texts]


class TestProviderAbstraction:
    def test_concrete_client_satisfies_interface(self) -> None:
        client = ConcreteClient()
        assert isinstance(client, BaseEmbeddingClient)

    def test_embed_returns_response(self) -> None:
        client = ConcreteClient()
        resp = client.embed(EmbeddingRequest(text="hello"))
        assert isinstance(resp, EmbeddingResponse)
        assert resp.provider == "test-provider"

    def test_embed_batch_returns_list(self) -> None:
        client = ConcreteClient()
        results = client.embed_batch(["a", "b", "c"])
        assert len(results) == 3
        assert all(isinstance(r, EmbeddingResponse) for r in results)

    def test_different_providers_can_coexist(self) -> None:
        """Two different provider implementations work side by side."""

        class ProviderA(BaseEmbeddingClient):
            @property
            def model(self) -> str:
                return "model-a"

            @property
            def provider_name(self) -> str:
                return "provider-a"

            def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
                return EmbeddingResponse(vector=[1.0], model=self.model, provider=self.provider_name)

            def embed_batch(self, texts: list[str]) -> list[EmbeddingResponse]:
                return [self.embed(EmbeddingRequest(text=t)) for t in texts]

        class ProviderB(BaseEmbeddingClient):
            @property
            def model(self) -> str:
                return "model-b"

            @property
            def provider_name(self) -> str:
                return "provider-b"

            def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
                return EmbeddingResponse(vector=[2.0], model=self.model, provider=self.provider_name)

            def embed_batch(self, texts: list[str]) -> list[EmbeddingResponse]:
                return [self.embed(EmbeddingRequest(text=t)) for t in texts]

        a, b = ProviderA(), ProviderB()
        assert a.embed(EmbeddingRequest("x")).provider == "provider-a"
        assert b.embed(EmbeddingRequest("x")).provider == "provider-b"

    def test_embedding_client_error_is_exception(self) -> None:
        err = EmbeddingClientError("something went wrong")
        assert isinstance(err, Exception)
        assert "something went wrong" in str(err)
