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

class TestLoaderIntegration:
    """Loader returns ExtractionRecord objects; absent directories return []."""

    def test_load_markdown_records_absent_dir(self, tmp_path) -> None:
        from extractors.loader import load_markdown_records
        records = load_markdown_records(source_dir=tmp_path / "nonexistent")
        assert records == []

    def test_load_openapi_records_absent_dir(self, tmp_path) -> None:
        from extractors.loader import load_openapi_records
        records = load_openapi_records(source_dir=tmp_path / "nonexistent")
        assert records == []

    def test_load_java_records_absent_dir(self, tmp_path) -> None:
        from extractors.loader import load_java_records
        records = load_java_records(source_dir=tmp_path / "nonexistent")
        assert records == []

    def test_load_markdown_records_with_mock_reader(self, tmp_path) -> None:
        from extractors.loader import load_markdown_records

        fake_dir = tmp_path / "chunks"
        fake_dir.mkdir()

        mock_doc = MagicMock()
        mock_doc.text = "Payment initiation requires a valid consent."
        mock_doc.metadata = {"file_path": str(fake_dir / "psd2_chunk.md")}

        with patch("markdown_parser.reader.load_documents", return_value=[mock_doc]):
            records = load_markdown_records(source_dir=fake_dir)

        assert len(records) == 1
        assert records[0].source_parser == "markdown_parser"
        assert "Payment" in records[0].text

    def test_load_openapi_records_with_mock_reader(self, tmp_path) -> None:
        from extractors.loader import load_openapi_records

        fake_dir = tmp_path / "specs"
        fake_dir.mkdir()

        mock_doc = MagicMock()
        mock_doc.text = "openapi: 3.0.1\ninfo:\n  title: NextGenPSD2\n  version: 1.3"
        mock_doc.metadata = {"file_path": str(fake_dir / "nextgenpsd2.yaml")}

        with patch("openapi_parser.readers.read_local", return_value=[mock_doc]):
            records = load_openapi_records(source_dir=fake_dir)

        assert len(records) == 1
        assert records[0].source_parser == "openapi_parser"


# ---------------------------------------------------------------------------
# spaCy extraction integration tests
# ---------------------------------------------------------------------------

