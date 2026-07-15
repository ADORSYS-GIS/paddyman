"""Unit tests for the relationship normalisation pipeline."""
from __future__ import annotations

from uuid import UUID

from entities.models import CanonicalEntity
from relationships.normalizer import RelationshipNormalizer, normalize_relationships
from relationships.rules import RelationshipTypeMapper
from shared.models import Relationship


class TestRelationshipNormalizer:
    def test_java_calls_maps_to_uses(self, canonical_entities: list[CanonicalEntity]) -> None:
        raw = {
            "source": "PaymentController",
            "target": "PaymentService",
            "relationship_type": "CALLS",
            "repository": "xs2a",
            "module": "impl",
            "file_path": "PaymentController.java",
            "version_tag": "v2",
            "confidence": 0.8,
        }
        rel = normalize_relationships([raw], canonical_entities)[0]
        assert rel.type == "USES"
        assert rel.properties["source"] == "PaymentController"
        assert rel.properties["target"] == "PaymentService"
        assert rel.properties["original_type"] == "CALLS"
        assert rel.properties["source_parser"] == "java_parser"
        assert rel.properties["repository"] == "xs2a"

    def test_openapi_returns_maps_to_exposes(self, canonical_entities: list[CanonicalEntity]) -> None:
        raw = {
            "source": "POST /payments",
            "target": "PaymentDTO",
            "relationship": "RETURNS",
            "spec_source": "api.yaml",
            "endpoint_method": "POST",
            "endpoint_path": "/payments",
        }
        rel = normalize_relationships([raw], canonical_entities)[0]
        assert rel.type == "EXPOSES"
        assert rel.properties["target"] == "PaymentRequest"
        assert rel.properties["source_parser"] == "openapi_parser"
        assert rel.properties["file_path"] == "api.yaml"

    def test_multiple_source_types_are_supported(self, canonical_entities: list[CanonicalEntity]) -> None:
        raws = [
            {"source": "PaymentController", "target": "PaymentService", "relationship_type": "CALLS"},
            {"source": "PaymentService", "target": "PaymentRequest", "type": "DEPENDS_ON"},
            {"subject": "PaymentDocumentation", "predicate": "documents", "object_name": "PaymentRequest"},
            {"source": "PaymentRequest", "target": "PaymentDocumentation", "type": "references", "source_parser": "spacy"},
        ]
        relationships = normalize_relationships(raws, canonical_entities)
        assert [rel.type for rel in relationships] == ["DEPENDS_ON", "DOCUMENTS", "REFERENCES", "USES"]

    def test_metadata_preservation(self, canonical_entities: list[CanonicalEntity]) -> None:
        raw = {
            "source": "PaymentDocumentation",
            "target": "PaymentRequest",
            "type": "DOCUMENTS",
            "source_parser": "markdown_parser",
            "repository": "docs-repo",
            "module": "payments",
            "document": "payments.md",
            "file_path": "docs/payments.md",
            "version_tag": "v1",
            "confidence": 0.7,
        }
        rel = normalize_relationships([raw], canonical_entities)[0]
        provenance = rel.properties["provenance"][0]
        assert rel.properties["module"] == "payments"
        assert rel.properties["document"] == "payments.md"
        assert rel.properties["version_tag"] == "v1"
        assert rel.properties["confidence"] == 0.7
        assert provenance["source_parser"] == "markdown_parser"
        assert provenance["source_entity"] == "PaymentDocumentation"

    def test_unknown_relationship_type_is_preserved_and_mapped(self, canonical_entities: list[CanonicalEntity]) -> None:
        rel = normalize_relationships(
            [{"source": "PaymentDocumentation", "target": "PaymentRequest", "type": "MENTIONS"}],
            canonical_entities,
        )[0]
        assert rel.type == "REFERENCES"
        assert rel.properties["original_type"] == "MENTIONS"

    def test_configurable_mapping_rules(self, canonical_entities: list[CanonicalEntity]) -> None:
        normalizer = RelationshipNormalizer(RelationshipTypeMapper({"mentions": "documents"}))
        rel = normalizer.normalize(
            [{"source": "PaymentDocumentation", "target": "PaymentRequest", "type": "mentions"}],
            canonical_entities,
        )[0]
        assert rel.type == "DOCUMENTS"

    def test_duplicate_relationship_handling(self, canonical_entities: list[CanonicalEntity]) -> None:
        raws = [
            {"source": "PaymentController", "target": "PaymentService", "type": "CALLS", "confidence": 0.5},
            {"source": "PaymentController", "target": "PaymentService", "type": "USES", "confidence": 0.9},
        ]
        rel = normalize_relationships(raws, canonical_entities)[0]
        assert rel.type == "USES"
        assert rel.confidence == 0.9
        assert rel.properties["original_types"] == ["CALLS", "USES"]
        assert len(rel.properties["provenance"]) == 2

    def test_output_conforms_to_shared_relationship_model(self, canonical_entities: list[CanonicalEntity]) -> None:
        rel = normalize_relationships(
            [{"source": "PaymentController", "target": "PaymentService", "type": "USES"}],
            canonical_entities,
        )[0]
        assert isinstance(rel, Relationship)
        assert isinstance(rel.source_entity_id, UUID)
        assert isinstance(rel.target_entity_id, UUID)

    def test_shared_relationship_json_shape_is_supported(self, canonical_entities: list[CanonicalEntity]) -> None:
        rel = normalize_relationships(
            [{"source_entity_id": "source-uuid", "target_entity_id": "target-uuid", "type": "USES"}],
            canonical_entities,
        )[0]
        assert rel.type == "USES"
        assert rel.properties["source"] == "source-uuid"
        assert rel.properties["target"] == "target-uuid"