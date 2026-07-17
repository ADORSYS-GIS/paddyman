"""Tests for the EmbeddingResult model and EmbeddingMetadata."""
from __future__ import annotations

import pytest

from ..models.embedding_result import EmbeddingInputType, EmbeddingMetadata, EmbeddingResult


def _make_metadata(**overrides) -> EmbeddingMetadata:
    defaults = dict(
        embedding_model="qwen3-embedding-8b",
        embedding_provider="openai_compat",
        vector_dimension=4,
        source_parser="java_parser",
        repository="aspsp-xs2a",
    )
    return EmbeddingMetadata(**{**defaults, **overrides})


class TestEmbeddingResult:
    def test_to_dict_contains_required_keys(self) -> None:
        result = EmbeddingResult(
            entity="Payment",
            input_type=EmbeddingInputType.ENTITY,
            source_id="src-1",
            vector=[0.1, 0.2],
            metadata=_make_metadata(vector_dimension=2),
        )
        d = result.to_dict()
        assert d["entity"] == "Payment"
        assert d["vector"] == [0.1, 0.2]
        assert "metadata" in d
        assert d["metadata"]["embedding_model"] == "qwen3-embedding-8b"
        assert d["metadata"]["vector_dimension"] == 2
        assert d["metadata"]["source_parser"] == "java_parser"

    def test_input_type_enum_values(self) -> None:
        assert EmbeddingInputType.ENTITY.value == "entity"
        assert EmbeddingInputType.JAVA_CLASS.value == "java_class"
        assert EmbeddingInputType.API_ENDPOINT.value == "api_endpoint"
        assert EmbeddingInputType.MARKDOWN_SECTION.value == "markdown_section"
        assert EmbeddingInputType.OPENAPI_SCHEMA.value == "openapi_schema"

    def test_empty_vector_allowed(self) -> None:
        result = EmbeddingResult(
            entity="Failed",
            input_type=EmbeddingInputType.CHUNK,
            source_id="s",
            vector=[],
            metadata=_make_metadata(vector_dimension=0),
        )
        d = result.to_dict()
        assert d["vector"] == []

    def test_metadata_defaults_are_empty_strings(self) -> None:
        m = EmbeddingMetadata(
            embedding_model="m",
            embedding_provider="p",
            vector_dimension=8,
        )
        assert m.source_parser == ""
        assert m.repository == ""
        assert m.file_path == ""
