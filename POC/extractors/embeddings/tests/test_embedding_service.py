"""Tests for EmbeddingService — entity and chunk embedding generation."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from ..client.base_client import EmbeddingClientError
from ..models.embedding_result import EmbeddingInputType, EmbeddingResult
from ..services.embedding_service import EmbeddingService


class TestEmbedEntity:
    def test_returns_embedding_result(self, mock_embedding_client, payment_entity, java_source):
        service = EmbeddingService(client=mock_embedding_client, retry_delay=0)
        result = service.embed_entity(payment_entity, java_source, source_parser="java_parser")

        assert isinstance(result, EmbeddingResult)
        assert result.entity == "PaymentService"
        assert result.vector == [0.1, 0.2, 0.3, 0.4]
        assert result.input_type == EmbeddingInputType.JAVA_CLASS

    def test_metadata_populated(self, mock_embedding_client, payment_entity, java_source):
        service = EmbeddingService(client=mock_embedding_client, retry_delay=0)
        result = service.embed_entity(payment_entity, java_source, source_parser="java_parser")

        m = result.metadata
        assert m.source_parser == "java_parser"
        assert m.repository == "aspsp-xs2a"
        assert m.module == "payments"
        assert m.version_tag == "2"
        assert m.vector_dimension == 4
        assert m.embedding_model == "qwen3-embedding-8b"
        assert m.embedding_provider == "openai_compat"

    def test_endpoint_entity_maps_to_api_endpoint_type(
        self, mock_embedding_client, endpoint_entity, openapi_source
    ):
        service = EmbeddingService(client=mock_embedding_client, retry_delay=0)
        result = service.embed_entity(endpoint_entity, openapi_source)

        assert result.input_type == EmbeddingInputType.API_ENDPOINT

    def test_unknown_entity_type_defaults_to_entity(
        self, mock_embedding_client, java_source
    ):
        from shared.models import Entity
        ent = Entity(type="CustomType", name="Foo", source="some-src")
        service = EmbeddingService(client=mock_embedding_client, retry_delay=0)
        result = service.embed_entity(ent, java_source)

        assert result.input_type == EmbeddingInputType.ENTITY

    def test_returns_empty_vector_on_exhausted_retries(
        self, payment_entity, java_source
    ):
        bad_client = MagicMock()
        bad_client.model = "m"
        bad_client.provider_name = "p"
        bad_client.embed.side_effect = EmbeddingClientError("down")
        service = EmbeddingService(client=bad_client, max_retries=1, retry_delay=0)
        result = service.embed_entity(payment_entity, java_source)

        assert result.vector == []
        assert result.metadata.vector_dimension == 0


class TestEmbedChunk:
    def test_chunk_returns_correct_input_type(
        self, mock_embedding_client, markdown_source
    ):
        service = EmbeddingService(client=mock_embedding_client, retry_delay=0)
        result = service.embed_chunk(
            text="Introduction to PSD2",
            label="Introduction",
            input_type=EmbeddingInputType.MARKDOWN_SECTION,
            source_metadata=markdown_source,
            source_parser="markdown_parser",
        )

        assert result.input_type == EmbeddingInputType.MARKDOWN_SECTION
        assert result.entity == "Introduction"
        assert len(result.vector) == 4

    def test_chunk_empty_text_still_calls_client(
        self, mock_embedding_client, markdown_source
    ):
        service = EmbeddingService(client=mock_embedding_client, retry_delay=0)
        result = service.embed_chunk(
            text="",
            label="empty",
            input_type=EmbeddingInputType.CHUNK,
            source_metadata=markdown_source,
        )
        mock_embedding_client.embed.assert_called_once()
        assert isinstance(result, EmbeddingResult)

    def test_to_dict_is_serialisable(self, mock_embedding_client, markdown_source):
        service = EmbeddingService(client=mock_embedding_client, retry_delay=0)
        result = service.embed_chunk(
            text="some text",
            label="SomeSection",
            input_type=EmbeddingInputType.MARKDOWN_SECTION,
            source_metadata=markdown_source,
        )
        d = result.to_dict()
        assert d["entity"] == "SomeSection"
        assert isinstance(d["vector"], list)
        assert "embedding_model" in d["metadata"]
