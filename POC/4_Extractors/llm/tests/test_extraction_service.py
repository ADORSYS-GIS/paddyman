"""Tests for ExtractionService — orchestration, retries, and error handling."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, call

import pytest

from client.base_client import CompletionResponse, LLMClientError
from services.extraction_service import ExtractionService
from shared.models import ExtractionStatus, SourceMetadata, SourceType


def _src(sid: str = "test") -> SourceMetadata:
    return SourceMetadata(
        source_id=sid,
        source_type=SourceType.DOCUMENT,
        location="/docs/test.md",
        metadata={},
    )


def _resp(content: str) -> CompletionResponse:
    return CompletionResponse(content=content, model="glm-4-flash")


_VALID_JSON = json.dumps({
    "entities": [{"type": "entity", "name": "Payment", "label": "DOMAIN_ENTITY"}],
    "relationships": [],
})

_EMPTY_JSON = json.dumps({"entities": [], "relationships": []})


class TestExtractionServiceSuccess:
    def test_returns_extraction_result(self, mock_llm_client) -> None:
        mock_llm_client.complete.return_value = _resp(_VALID_JSON)
        svc = ExtractionService(mock_llm_client, max_retries=0, retry_delay=0)
        result = svc.run("Payment approved.", _src())
        assert result.status == ExtractionStatus.SUCCESS

    def test_entities_extracted(self, mock_llm_client) -> None:
        mock_llm_client.complete.return_value = _resp(_VALID_JSON)
        svc = ExtractionService(mock_llm_client, max_retries=0, retry_delay=0)
        result = svc.run("Payment approved.", _src())
        assert len(result.entities) == 1
        assert result.entities[0].name == "Payment"

    def test_source_parser_propagated(self, mock_llm_client) -> None:
        mock_llm_client.complete.return_value = _resp(_VALID_JSON)
        svc = ExtractionService(mock_llm_client, max_retries=0, retry_delay=0)
        result = svc.run("text", _src(), source_parser="java_parser")
        assert result.entities[0].properties["source_parser"] == "java_parser"

    def test_source_metadata_in_result(self, mock_llm_client) -> None:
        mock_llm_client.complete.return_value = _resp(_EMPTY_JSON)
        svc = ExtractionService(mock_llm_client, max_retries=0, retry_delay=0)
        src = _src("my-source")
        result = svc.run("text", src)
        assert result.source.source_id == "my-source"

    def test_accepts_java_parser_output(self, java_source, mock_llm_client) -> None:
        mock_llm_client.complete.return_value = _resp(_VALID_JSON)
        svc = ExtractionService(mock_llm_client, max_retries=0, retry_delay=0)
        result = svc.run("public class PaymentController {}", java_source, "java_parser")
        assert result.source.source_id == java_source.source_id

    def test_accepts_openapi_parser_output(self, openapi_source, mock_llm_client) -> None:
        mock_llm_client.complete.return_value = _resp(_EMPTY_JSON)
        svc = ExtractionService(mock_llm_client, max_retries=0, retry_delay=0)
        result = svc.run("paths:\n  /payments: {}", openapi_source, "openapi_parser")
        assert isinstance(result.status, ExtractionStatus)

    def test_accepts_markdown_parser_output(self, markdown_source, mock_llm_client) -> None:
        mock_llm_client.complete.return_value = _resp(_EMPTY_JSON)
        svc = ExtractionService(mock_llm_client, max_retries=0, retry_delay=0)
        result = svc.run("## Payment Service\nHandles PSD2.", markdown_source, "markdown_parser")
        assert isinstance(result.status, ExtractionStatus)


class TestExtractionServiceRetry:
    def test_retries_on_llm_client_error(self, mock_llm_client) -> None:
        mock_llm_client.complete.side_effect = [
            LLMClientError("timeout"),
            _resp(_VALID_JSON),
        ]
        svc = ExtractionService(mock_llm_client, max_retries=1, retry_delay=0)
        result = svc.run("text", _src())
        assert result.status == ExtractionStatus.SUCCESS
        assert mock_llm_client.complete.call_count == 2

    def test_all_retries_exhausted_returns_failed(self, mock_llm_client) -> None:
        mock_llm_client.complete.side_effect = LLMClientError("server error")
        svc = ExtractionService(mock_llm_client, max_retries=2, retry_delay=0)
        result = svc.run("text", _src())
        assert result.status == ExtractionStatus.FAILED
        assert result.errors
        assert mock_llm_client.complete.call_count == 3  # 1 + 2 retries

    def test_failed_result_has_source(self, mock_llm_client) -> None:
        mock_llm_client.complete.side_effect = LLMClientError("fail")
        svc = ExtractionService(mock_llm_client, max_retries=0, retry_delay=0)
        src = _src("fail-src")
        result = svc.run("text", src)
        assert result.source.source_id == "fail-src"


class TestExtractionServiceMalformedResponse:
    def test_malformed_json_returns_failed(self, mock_llm_client) -> None:
        mock_llm_client.complete.return_value = _resp("not json")
        svc = ExtractionService(mock_llm_client, max_retries=0, retry_delay=0)
        result = svc.run("text", _src())
        assert result.status == ExtractionStatus.FAILED
        assert result.errors

    def test_pipeline_continues_on_empty_response(self, mock_llm_client) -> None:
        mock_llm_client.complete.return_value = _resp(_EMPTY_JSON)
        svc = ExtractionService(mock_llm_client, max_retries=0, retry_delay=0)
        result = svc.run("text", _src())
        assert result.status == ExtractionStatus.PARTIAL
        assert not result.errors
