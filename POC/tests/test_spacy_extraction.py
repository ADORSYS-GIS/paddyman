"""Integration tests — Phase 4 Entity Extraction pipeline.

Tests validate complete extractor pipeline execution, parser output consumption,
spaCy/LLM/embedding integration, and failure handling. External provider calls
are mocked; spaCy uses a real minimal pipeline.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from shared.models import (
    Entity,
    ExtractionResult,
    ExtractionStatus,
    SourceMetadata,
    SourceType,
)
from extractors.embeddings.models.embedding_result import EmbeddingInputType
from extractors.llm.client.base_client import LLMClientError

class TestSpacyExtractionIntegration:
    """spaCy pipeline produces entities with version tags from parser outputs."""

    def test_spacy_extracts_entities_from_markdown(self, markdown_source) -> None:
        from extractors.spacy.pipeline.pipeline import SpacyExtractionPipeline

        nlp = SpacyExtractionPipeline.build()
        text = "The Payment API supports Account access via Consent v1.3."
        result = nlp.run(text=text, source_metadata=markdown_source, source_parser="markdown_parser")

        assert result.status in (ExtractionStatus.SUCCESS, ExtractionStatus.PARTIAL)
        assert all(isinstance(e, Entity) for e in result.entities)

    def test_spacy_version_tag_injected(self) -> None:
        from extractors.spacy.pipeline.pipeline import SpacyExtractionPipeline

        meta = SourceMetadata(
            source_id="nextgenpsd2_1_3",
            source_type=SourceType.API,
            location="/specs/nextgenpsd2_1_3/openapi.yaml",
            metadata={"file_path": "/specs/nextgenpsd2_1_3/openapi.yaml", "module": "nextgenpsd2_1_3"},
        )
        nlp = SpacyExtractionPipeline.build()
        result = nlp.run(text="Payment Consent Account", source_metadata=meta)

        for entity in result.entities:
            version = entity.properties.get("version")
            if version:
                assert version.startswith("v")

    def test_spacy_empty_text_does_not_raise(self, markdown_source) -> None:
        from extractors.spacy.pipeline.pipeline import SpacyExtractionPipeline

        nlp = SpacyExtractionPipeline.build()
        result = nlp.run(text="", source_metadata=markdown_source)
        assert isinstance(result, ExtractionResult)


# ---------------------------------------------------------------------------
# GLM extraction integration tests
# ---------------------------------------------------------------------------

