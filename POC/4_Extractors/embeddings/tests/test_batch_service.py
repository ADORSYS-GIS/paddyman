"""Tests for BatchEmbeddingService — bulk entity and chunk embedding."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from client.base_client import EmbeddingClientError, EmbeddingResponse
from models.embedding_result import EmbeddingInputType, EmbeddingResult
from services.batch_service import BatchEmbeddingService
from shared.models import Entity


def _make_response(vector: list[float]) -> EmbeddingResponse:
    return EmbeddingResponse(
        vector=vector, model="qwen3-embedding-8b", provider="openai_compat"
    )


class TestBatchEmbedEntities:
    def test_embed_entities_returns_one_result_per_entity(
        self, mock_embedding_client, java_source
    ):
        entities = [
            Entity(type="class", name="PaymentService", source="src"),
            Entity(type="method", name="initiatePayment", source="src"),
        ]
        mock_embedding_client.embed_batch.return_value = [
            _make_response([0.1, 0.2]),
            _make_response([0.3, 0.4]),
        ]
        service = BatchEmbeddingService(
            client=mock_embedding_client, batch_size=10, retry_delay=0
        )
        results = service.embed_entities(entities, java_source, source_parser="java_parser")

        assert len(results) == 2
        assert results[0].entity == "PaymentService"
        assert results[0].input_type == EmbeddingInputType.JAVA_CLASS
        assert results[1].entity == "initiatePayment"
        assert results[1].input_type == EmbeddingInputType.JAVA_METHOD

    def test_embed_entities_empty_list(self, mock_embedding_client, java_source):
        service = BatchEmbeddingService(client=mock_embedding_client, retry_delay=0)
        assert service.embed_entities([], java_source) == []
        mock_embedding_client.embed_batch.assert_not_called()

    def test_batch_size_respected(self, mock_embedding_client, java_source):
        """With batch_size=1, embed_batch is called once per entity."""
        entities = [
            Entity(type="class", name="A", source="s"),
            Entity(type="class", name="B", source="s"),
        ]
        mock_embedding_client.embed_batch.return_value = [_make_response([0.1])]
        service = BatchEmbeddingService(
            client=mock_embedding_client, batch_size=1, retry_delay=0
        )
        results = service.embed_entities(entities, java_source)

        assert mock_embedding_client.embed_batch.call_count == 2
        assert len(results) == 2


class TestBatchEmbedChunks:
    def test_embed_chunks_returns_correct_types(
        self, mock_embedding_client, markdown_source
    ):
        chunks = [
            {"text": "Intro text", "label": "Intro", "input_type": "markdown_section"},
            {"text": "Body text", "label": "Body"},
        ]
        mock_embedding_client.embed_batch.return_value = [
            _make_response([0.1, 0.2]),
            _make_response([0.3, 0.4]),
        ]
        service = BatchEmbeddingService(
            client=mock_embedding_client, batch_size=10, retry_delay=0
        )
        results = service.embed_chunks(
            chunks, markdown_source, source_parser="markdown_parser"
        )

        assert results[0].input_type == EmbeddingInputType.MARKDOWN_SECTION
        assert results[1].input_type == EmbeddingInputType.CHUNK

    def test_embed_chunks_empty_list(self, mock_embedding_client, markdown_source):
        service = BatchEmbeddingService(client=mock_embedding_client, retry_delay=0)
        assert service.embed_chunks([], markdown_source) == []


class TestBatchRetryAndErrorHandling:
    def test_returns_empty_vectors_on_exhausted_retries(
        self, java_source
    ):
        bad_client = MagicMock()
        bad_client.model = "m"
        bad_client.provider_name = "p"
        bad_client.embed_batch.side_effect = EmbeddingClientError("down")

        entities = [Entity(type="class", name="X", source="s")]
        service = BatchEmbeddingService(
            client=bad_client, batch_size=10, max_retries=1, retry_delay=0
        )
        results = service.embed_entities(entities, java_source)

        assert len(results) == 1
        assert results[0].vector == []

    def test_metadata_source_parser_propagated(
        self, mock_embedding_client, java_source
    ):
        mock_embedding_client.embed_batch.return_value = [_make_response([0.9])]
        entities = [Entity(type="class", name="Foo", source="s")]
        service = BatchEmbeddingService(
            client=mock_embedding_client, batch_size=10, retry_delay=0
        )
        results = service.embed_entities(entities, java_source, source_parser="java_parser")
        assert results[0].metadata.source_parser == "java_parser"
