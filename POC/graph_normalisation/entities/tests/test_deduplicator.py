"""Unit tests for the canonical entity deduplicator."""
from __future__ import annotations

import logging

from shared.models import Entity

from entities import deduplicate_entities
from entities.deduplicator import EntityDeduplicator
from entities.models import CanonicalEntity, EntitySource


def _source(parser: str, name: str, repository: str = "repo") -> EntitySource:
    raw = Entity(type="concept", name=name, source=parser)
    return EntitySource(
        source_parser=parser,
        original_name=name,
        repository=repository,
        module="module-a",
        document="doc.md",
        file_path=f"/{parser}/{name}.txt",
        version_tag="v1",
        confidence=0.8,
        entity_ref=raw,
    )


def _canonical(
    entity_id: str,
    aliases: list[str],
    parser: str,
    confidence: float = 0.8,
    properties: dict | None = None,
    entity_type: str = "domain_entity",
) -> CanonicalEntity:
    return CanonicalEntity(
        id=entity_id,
        type=entity_type,
        aliases=aliases,
        sources=[_source(parser, aliases[0] if aliases else entity_id)],
        confidence=confidence,
        properties=properties or {},
    )


class TestEntityDeduplicator:
    def test_exact_duplicate_detection(self) -> None:
        entities = [
            _canonical("PaymentRequest", ["PaymentRequest"], "openapi_parser"),
            _canonical("PaymentRequestCopy", ["Payment Request"], "markdown_parser"),
        ]
        result = deduplicate_entities(entities)
        assert len(result) == 1
        assert {s.source_parser for s in result[0].sources} == {"openapi_parser", "markdown_parser"}

    def test_name_similarity_matching(self) -> None:
        entities = [
            _canonical("ConsentRequest", ["ConsentRequest"], "java_parser"),
            _canonical("ConsentRequests", ["Consent Requests"], "openapi_parser"),
        ]
        result = EntityDeduplicator().deduplicate(entities)
        assert len(result) == 1
        assert set(result[0].aliases) >= {"ConsentRequest", "ConsentRequests", "Consent Requests"}

    def test_embedding_similarity_matching(self) -> None:
        entities = [
            _canonical("PaymentCommand", ["Payment Command"], "llm", properties={"embedding": [1, 0]}),
            _canonical("InitiatePayment", ["Initiate Payment"], "spacy", properties={"embedding": [0.99, 0.01]}),
        ]
        result = deduplicate_entities(entities)
        assert len(result) == 1
        assert result[0].properties["embedding"] == [1, 0]

    def test_domain_rule_matching_uses_payment_request_example(self) -> None:
        entities = [
            _canonical("PaymentDTO", ["PaymentDTO"], "java_parser", confidence=0.9),
            _canonical("PaymentRequest", ["PaymentRequest"], "openapi_parser", confidence=0.9),
            _canonical("PaymentInitiationRequest", ["Payment Initiation Request"], "markdown_parser", confidence=0.9),
        ]
        result = deduplicate_entities(entities)
        assert len(result) == 1
        assert result[0].id == "PaymentRequest"
        assert result[0].aliases == [
            "PaymentDTO",
            "PaymentRequest",
            "PaymentInitiationRequest",
            "Payment Initiation Request",
        ]

    def test_metadata_preservation(self) -> None:
        entities = [
            _canonical("PaymentDTO", ["PaymentDTO"], "java_parser"),
            _canonical("PaymentRequest", ["PaymentRequest"], "openapi_parser"),
        ]
        merged = deduplicate_entities(entities)[0]
        assert len(merged.sources) == 2
        assert {source.repository for source in merged.sources} == {"repo"}
        assert {source.module for source in merged.sources} == {"module-a"}
        assert {source.document for source in merged.sources} == {"doc.md"}
        assert {source.version_tag for source in merged.sources} == {"v1"}
        assert len(merged.properties["original_entity_ids"]) == 2
        assert merged.to_dict()["sources"][0]["entity_id"] is not None

    def test_conflicting_entity_handling(self, caplog) -> None:  # type: ignore[no-untyped-def]
        caplog.set_level(logging.WARNING)
        result = deduplicate_entities(
            [
                _canonical("PaymentDTO", ["PaymentDTO"], "java_parser", entity_type="domain_entity"),
                _canonical("PaymentRequest", ["PaymentRequest"], "openapi_parser", entity_type="api_schema"),
            ]
        )
        assert len(result) == 1
        assert "Conflicting entity types" in caplog.text

    def test_non_duplicates_remain_separate(self) -> None:
        result = deduplicate_entities(
            [
                _canonical("PaymentRequest", ["PaymentRequest"], "openapi_parser"),
                _canonical("AccountInformation", ["Account Information"], "markdown_parser"),
            ]
        )
        assert [entity.id for entity in result] == ["AccountInformation", "PaymentRequest"]