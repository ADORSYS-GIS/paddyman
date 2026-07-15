"""Tests for the LLM response parser."""
from __future__ import annotations

import json

import pytest

from parser.response_parser import ResponseParser
from shared.models import ExtractionResult, ExtractionStatus, SourceMetadata, SourceType

_PARSER = ResponseParser()


def _src(sid: str = "test") -> SourceMetadata:
    return SourceMetadata(
        source_id=sid,
        source_type=SourceType.DOCUMENT,
        location="/docs/test.md",
        metadata={},
    )


def _json(**kwargs) -> str:
    return json.dumps({"entities": [], "relationships": [], **kwargs})


class TestParseValidJSON:
    def test_empty_entities_and_relationships(self) -> None:
        result = _PARSER.parse(_json(), _src())
        assert isinstance(result, ExtractionResult)
        assert result.status == ExtractionStatus.PARTIAL
        assert result.entities == []
        assert result.relationships == []

    def test_entity_extracted(self) -> None:
        payload = _json(entities=[{"type": "entity", "name": "Payment", "label": "DOMAIN_ENTITY"}])
        result = _PARSER.parse(payload, _src())
        assert len(result.entities) == 1
        assert result.entities[0].name == "Payment"
        assert result.entities[0].type == "entity"
        assert result.status == ExtractionStatus.SUCCESS

    def test_entity_label_preserved(self) -> None:
        payload = _json(entities=[{"name": "Consent", "label": "DOMAIN_ENTITY"}])
        result = _PARSER.parse(payload, _src())
        assert result.entities[0].properties["label"] == "DOMAIN_ENTITY"

    def test_source_parser_in_entity_properties(self) -> None:
        payload = _json(entities=[{"name": "Account", "label": "X"}])
        result = _PARSER.parse(payload, _src(), source_parser="openapi_parser")
        assert result.entities[0].properties["source_parser"] == "openapi_parser"

    def test_extraction_rule_is_llm(self) -> None:
        payload = _json(entities=[{"name": "Transaction", "label": "X"}])
        result = _PARSER.parse(payload, _src())
        assert result.entities[0].properties["extraction_rule"] == "llm"

    def test_relationship_extracted(self) -> None:
        payload = _json(
            entities=[
                {"name": "Payment", "label": "A"},
                {"name": "Account", "label": "B"},
            ],
            relationships=[
                {"source": "Payment", "target": "Account", "type": "USES", "confidence": 0.9}
            ],
        )
        result = _PARSER.parse(payload, _src())
        assert len(result.relationships) == 1
        assert result.relationships[0].type == "USES"
        assert result.relationships[0].confidence == 0.9

    def test_relationship_confidence_clamped(self) -> None:
        payload = _json(
            entities=[{"name": "A", "label": "X"}, {"name": "B", "label": "X"}],
            relationships=[{"source": "A", "target": "B", "type": "REL", "confidence": 99.0}],
        )
        result = _PARSER.parse(payload, _src())
        assert result.relationships[0].confidence == 1.0

    def test_json_in_markdown_fences(self) -> None:
        raw = "```json\n" + _json(entities=[{"name": "Consent", "label": "X"}]) + "\n```"
        result = _PARSER.parse(raw, _src())
        assert len(result.entities) == 1

    def test_json_in_plain_fences(self) -> None:
        raw = "```\n" + _json() + "\n```"
        result = _PARSER.parse(raw, _src())
        assert isinstance(result, ExtractionResult)


class TestParseInvalidJSON:
    def test_malformed_json_returns_failed(self) -> None:
        result = _PARSER.parse("not json at all", _src())
        assert result.status == ExtractionStatus.FAILED
        assert result.errors

    def test_json_array_at_root_returns_failed(self) -> None:
        result = _PARSER.parse("[]", _src())
        assert result.status == ExtractionStatus.FAILED

    def test_empty_string_returns_failed(self) -> None:
        result = _PARSER.parse("", _src())
        assert result.status == ExtractionStatus.FAILED


class TestParseEdgeCases:
    def test_entity_with_missing_name_skipped(self) -> None:
        payload = _json(entities=[{"label": "X"}])
        result = _PARSER.parse(payload, _src())
        assert result.entities == []
        assert result.warnings

    def test_relationship_unknown_source_skipped(self) -> None:
        payload = _json(
            entities=[{"name": "Account", "label": "X"}],
            relationships=[{"source": "Unknown", "target": "Account", "type": "REL"}],
        )
        result = _PARSER.parse(payload, _src())
        assert result.relationships == []
        assert result.warnings

    def test_relationship_unknown_target_skipped(self) -> None:
        payload = _json(
            entities=[{"name": "Payment", "label": "X"}],
            relationships=[{"source": "Payment", "target": "Missing", "type": "REL"}],
        )
        result = _PARSER.parse(payload, _src())
        assert result.relationships == []

    def test_incomplete_relationship_skipped(self) -> None:
        payload = _json(
            relationships=[{"source": "A", "type": "REL"}]  # missing target
        )
        result = _PARSER.parse(payload, _src())
        assert result.relationships == []
        assert result.warnings

    def test_non_dict_entity_skipped(self) -> None:
        payload = _json(entities=["not-a-dict"])
        result = _PARSER.parse(payload, _src())
        assert result.entities == []
        assert result.warnings

    def test_source_id_in_entity(self) -> None:
        payload = _json(entities=[{"name": "Payment", "label": "X"}])
        src = _src("special-src")
        result = _PARSER.parse(payload, src)
        assert result.entities[0].source == "special-src"

    def test_multiple_entities(self) -> None:
        payload = _json(entities=[
            {"name": "Payment", "label": "A"},
            {"name": "Consent", "label": "B"},
            {"name": "Account", "label": "C"},
        ])
        result = _PARSER.parse(payload, _src())
        assert len(result.entities) == 3
