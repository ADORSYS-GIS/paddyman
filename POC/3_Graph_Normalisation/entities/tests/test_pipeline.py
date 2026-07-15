"""Unit tests for the canonical entity normalisation pipeline."""
from __future__ import annotations

from shared.models import Entity, ExtractionResult, ExtractionStatus, SourceMetadata

from entities.pipeline import normalise_entities


class TestPipeline:
    def test_different_parser_inputs_merge_into_canonical_entity(
        self,
        java_entity: Entity,
        openapi_entity: Entity,
        markdown_entity: Entity,
        spacy_entity: Entity,
        llm_entity: Entity,
        basic_source_meta: SourceMetadata,
    ) -> None:
        result = ExtractionResult(
            source=basic_source_meta,
            entities=[java_entity, openapi_entity, markdown_entity, spacy_entity, llm_entity],
            status=ExtractionStatus.SUCCESS,
        )
        canonical = normalise_entities([result])
        assert len(canonical) == 1
        entity = canonical[0]
        assert entity.id == "PaymentInitiation"
        assert set(entity.aliases) == {
            "PaymentController",
            "POST /payments",
            "Payment Initiation",
            "Payment",
            "PaymentInitiation",
        }
        assert len(entity.sources) == 5

    def test_provenance_is_preserved(
        self,
        java_entity: Entity,
        openapi_entity: Entity,
        basic_source_meta: SourceMetadata,
    ) -> None:
        result = ExtractionResult(
            source=basic_source_meta,
            entities=[java_entity, openapi_entity],
            status=ExtractionStatus.SUCCESS,
        )
        entity = normalise_entities([result])[0]
        parsers = {s.source_parser for s in entity.sources}
        paths = {s.file_path for s in entity.sources}
        assert parsers == {"java_parser", "openapi_parser"}
        assert "DataSource/yaml_spec/psd2-api-1.3.yaml" in paths
        assert any(p and p.endswith("PaymentController.java") for p in paths)

    def test_duplicate_entity_detection(self, java_entity: Entity, basic_source_meta: SourceMetadata) -> None:
        duplicate = Entity(
            type="controller",
            name="PaymentController",
            source="java_parser",
            properties=java_entity.properties,
        )
        result = ExtractionResult(
            source=basic_source_meta,
            entities=[java_entity, duplicate],
            status=ExtractionStatus.SUCCESS,
        )
        entity = normalise_entities([result])[0]
        assert entity.id == "PaymentInitiation"
        assert entity.aliases == ["PaymentController"]
        assert len(entity.sources) == 2

    def test_output_is_json_serialisable_shape(self, extraction_result: ExtractionResult) -> None:
        entity = normalise_entities([extraction_result])[0]
        d = entity.to_dict()
        assert d["id"] == "PaymentInitiation"
        assert "aliases" in d
        assert "sources" in d
        assert d["sources"][0]["entity_ref"] is None if "entity_ref" in d["sources"][0] else True

    def test_empty_results_are_supported(self) -> None:
        assert normalise_entities([]) == []