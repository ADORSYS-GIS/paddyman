"""Unit tests for EntitySourceAdapter provenance preservation."""
from __future__ import annotations

from shared.models import Entity

from entities.adapter import EntitySourceAdapter


class TestEntitySourceAdapter:
    def test_preserves_java_provenance(self, java_entity: Entity) -> None:
        source = EntitySourceAdapter().adapt(java_entity)
        assert source.source_parser == "java_parser"
        assert source.original_name == "PaymentController"
        assert source.repository == "aspsp-xs2a"
        assert source.module == "xs2a-impl"
        assert source.file_path.endswith("PaymentController.java")
        assert source.version_tag == "v2"
        assert source.confidence == 1.0
        assert source.entity_ref is java_entity

    def test_preserves_openapi_document_fields(self, openapi_entity: Entity) -> None:
        source = EntitySourceAdapter().adapt(openapi_entity)
        assert source.source_parser == "openapi_parser"
        assert source.document == "Berlin Group PSD2 AIS API"
        assert source.file_path == "DataSource/yaml_spec/psd2-api-1.3.yaml"
        assert source.version_tag == "1.3"

    def test_uses_entity_source_when_parser_missing(self) -> None:
        entity = Entity(type="concept", name="Payment", source="spacy", properties={})
        source = EntitySourceAdapter().adapt(entity)
        assert source.source_parser == "spacy"

    def test_invalid_confidence_defaults_to_one(self) -> None:
        entity = Entity(
            type="concept",
            name="Payment",
            source="spacy",
            properties={"confidence": "not-a-number"},
        )
        assert EntitySourceAdapter().adapt(entity).confidence == 1.0