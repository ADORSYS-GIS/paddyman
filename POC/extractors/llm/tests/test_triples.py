"""Unit tests for triple generation and the TripleService (Chunk 4.4)."""
from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from shared.models import (
    Entity,
    ExtractionResult,
    ExtractionStatus,
    Relationship,
    SourceMetadata,
)
from ..triples.triple_builder import Triple, TripleBuilder
from ..services.triple_service import TripleService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity(name: str, source_parser: str = "java_parser", source: str = "src") -> Entity:
    return Entity(
        type="entity",
        name=name,
        source=source,
        properties={"label": "CLASS", "source_parser": source_parser},
    )


def _result(
    source: SourceMetadata,
    entities: list[Entity],
    relationships: list[Relationship],
    status: ExtractionStatus = ExtractionStatus.SUCCESS,
) -> ExtractionResult:
    return ExtractionResult(
        source=source, entities=entities, relationships=relationships, status=status
    )


def _rel(
    src: Entity,
    tgt: Entity,
    rel_type: str,
    confidence: float = 1.0,
) -> Relationship:
    return Relationship(
        source_entity_id=src.id,
        target_entity_id=tgt.id,
        type=rel_type,
        confidence=confidence,
    )


# ---------------------------------------------------------------------------
# TripleBuilder
# ---------------------------------------------------------------------------

class TestTripleBuilder:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.builder = TripleBuilder()

    def test_basic_triple_generated(self, java_source: SourceMetadata) -> None:
        e1, e2 = _entity("PaymentInitiation"), _entity("PaymentService")
        result = _result(java_source, [e1, e2], [_rel(e1, e2, "USES")])
        triples = self.builder.build(result)
        assert len(triples) == 1
        assert triples[0].subject == "PaymentInitiation"
        assert triples[0].predicate == "USES"
        assert triples[0].object_name == "PaymentService"

    def test_multiple_relationships_produce_multiple_triples(
        self, java_source: SourceMetadata
    ) -> None:
        e1 = _entity("PaymentController")
        e2 = _entity("PaymentService")
        e3 = _entity("ConsentService")
        rels = [_rel(e1, e2, "CALLS"), _rel(e1, e3, "USES")]
        result = _result(java_source, [e1, e2, e3], rels)
        triples = self.builder.build(result)
        assert len(triples) == 2
        assert {t.predicate for t in triples} == {"CALLS", "USES"}

    def test_all_standard_predicate_types(self, java_source: SourceMetadata) -> None:
        rel_types = ["USES", "CALLS", "IMPLEMENTS", "EXTENDS", "RETURNS", "ACCEPTS", "REFERENCES"]
        entities = [_entity(f"E{i}") for i in range(len(rel_types) * 2)]
        rels = [
            _rel(entities[i * 2], entities[i * 2 + 1], rt)
            for i, rt in enumerate(rel_types)
        ]
        result = _result(java_source, entities, rels)
        triples = self.builder.build(result)
        assert {t.predicate for t in triples} == set(rel_types)

    def test_predicate_normalised_to_upper_case(
        self, java_source: SourceMetadata
    ) -> None:
        e1, e2 = _entity("A"), _entity("B")
        result = _result(java_source, [e1, e2], [_rel(e1, e2, "uses")])
        triples = self.builder.build(result)
        assert triples[0].predicate == "USES"

    def test_unknown_relationship_type_preserved(
        self, java_source: SourceMetadata
    ) -> None:
        e1, e2 = _entity("A"), _entity("B")
        result = _result(java_source, [e1, e2], [_rel(e1, e2, "TRIGGERS")])
        triples = self.builder.build(result)
        assert triples[0].predicate == "TRIGGERS"

    # ----- duplicate handling -----

    def test_duplicate_triple_deduplicated(self, java_source: SourceMetadata) -> None:
        e1, e2 = _entity("A"), _entity("B")
        rels = [_rel(e1, e2, "USES", 0.6), _rel(e1, e2, "USES", 0.9)]
        result = _result(java_source, [e1, e2], rels)
        triples = self.builder.build(result)
        assert len(triples) == 1

    def test_duplicate_keeps_highest_confidence(
        self, java_source: SourceMetadata
    ) -> None:
        e1, e2 = _entity("A"), _entity("B")
        rels = [_rel(e1, e2, "USES", 0.5), _rel(e1, e2, "USES", 0.8)]
        result = _result(java_source, [e1, e2], rels)
        assert self.builder.build(result)[0].confidence == 0.8

    def test_different_predicate_same_entities_not_deduplicated(
        self, java_source: SourceMetadata
    ) -> None:
        e1, e2 = _entity("A"), _entity("B")
        rels = [_rel(e1, e2, "USES"), _rel(e1, e2, "CALLS")]
        result = _result(java_source, [e1, e2], rels)
        assert len(self.builder.build(result)) == 2

    # ----- missing entities -----

    def test_missing_source_entity_skipped(
        self, java_source: SourceMetadata
    ) -> None:
        e2 = _entity("Target")
        orphan_rel = Relationship(
            source_entity_id=uuid4(), target_entity_id=e2.id, type="USES"
        )
        result = _result(java_source, [e2], [orphan_rel])
        assert self.builder.build(result) == []

    def test_missing_target_entity_skipped(
        self, java_source: SourceMetadata
    ) -> None:
        e1 = _entity("Source")
        orphan_rel = Relationship(
            source_entity_id=e1.id, target_entity_id=uuid4(), type="CALLS"
        )
        result = _result(java_source, [e1], [orphan_rel])
        assert self.builder.build(result) == []

    def test_empty_result_returns_empty_list(
        self, java_source: SourceMetadata
    ) -> None:
        result = _result(java_source, [], [])
        assert self.builder.build(result) == []

    def test_entities_without_relationships_returns_empty(
        self, java_source: SourceMetadata
    ) -> None:
        result = _result(java_source, [_entity("A"), _entity("B")], [])
        assert self.builder.build(result) == []

    # ----- confidence -----

    def test_confidence_preserved(self, java_source: SourceMetadata) -> None:
        e1, e2 = _entity("A"), _entity("B")
        result = _result(java_source, [e1, e2], [_rel(e1, e2, "EXTENDS", 0.73)])
        assert self.builder.build(result)[0].confidence == 0.73

    def test_default_confidence_is_one(self, java_source: SourceMetadata) -> None:
        e1, e2 = _entity("A"), _entity("B")
        result = _result(java_source, [e1, e2], [_rel(e1, e2, "USES")])
        assert self.builder.build(result)[0].confidence == 1.0

    # ----- metadata -----

    def test_metadata_source_document(self, java_source: SourceMetadata) -> None:
        e1, e2 = _entity("A"), _entity("B")
        result = _result(java_source, [e1, e2], [_rel(e1, e2, "USES")])
        assert self.builder.build(result)[0].metadata["source_document"] == "aspsp-xs2a"

    def test_metadata_repository(self, java_source: SourceMetadata) -> None:
        e1, e2 = _entity("A"), _entity("B")
        result = _result(java_source, [e1, e2], [_rel(e1, e2, "USES")])
        assert self.builder.build(result)[0].metadata["repository"] == "aspsp-xs2a"

    def test_metadata_module(self, java_source: SourceMetadata) -> None:
        e1, e2 = _entity("A"), _entity("B")
        result = _result(java_source, [e1, e2], [_rel(e1, e2, "USES")])
        assert self.builder.build(result)[0].metadata["module"] == "payments"

    def test_metadata_file_path(self, java_source: SourceMetadata) -> None:
        e1, e2 = _entity("A"), _entity("B")
        result = _result(java_source, [e1, e2], [_rel(e1, e2, "USES")])
        meta = self.builder.build(result)[0].metadata
        assert "file_path" in meta
        assert meta["file_path"] is not None

    def test_metadata_source_parser_from_entity(
        self, java_source: SourceMetadata
    ) -> None:
        e1 = _entity("A", source_parser="openapi_parser")
        e2 = _entity("B")
        result = _result(java_source, [e1, e2], [_rel(e1, e2, "RETURNS")])
        assert self.builder.build(result)[0].metadata["source_parser"] == "openapi_parser"

    def test_metadata_source_parser_absent_when_not_set(
        self, java_source: SourceMetadata
    ) -> None:
        e1 = Entity(type="entity", name="A", source="s", properties={})
        e2 = Entity(type="entity", name="B", source="s", properties={})
        result = _result(java_source, [e1, e2], [_rel(e1, e2, "USES")])
        assert "source_parser" not in self.builder.build(result)[0].metadata

    def test_openapi_source_metadata_preserved(
        self, openapi_source: SourceMetadata
    ) -> None:
        e1, e2 = _entity("Payment"), _entity("Account")
        result = _result(openapi_source, [e1, e2], [_rel(e1, e2, "REFERENCES")])
        meta = self.builder.build(result)[0].metadata
        assert meta["repository"] == "berlin-group"
        assert meta["source_document"] == "berlin-group-api"

    def test_markdown_source_metadata_preserved(
        self, markdown_source: SourceMetadata
    ) -> None:
        e1, e2 = _entity("Consent"), _entity("Payment")
        result = _result(markdown_source, [e1, e2], [_rel(e1, e2, "USES")])
        assert self.builder.build(result)[0].metadata["source_document"] == "psd2-guidelines"

    def test_relationship_backref_set(self, java_source: SourceMetadata) -> None:
        e1, e2 = _entity("A"), _entity("B")
        rel = _rel(e1, e2, "CALLS")
        result = _result(java_source, [e1, e2], [rel])
        assert self.builder.build(result)[0].relationship is rel


# ---------------------------------------------------------------------------
# TripleService (integration via mocked ExtractionService)
# ---------------------------------------------------------------------------

class TestTripleService:
    @pytest.fixture()
    def mock_client(self) -> MagicMock:
        return MagicMock()

    def _service_with_result(
        self, mock_client: MagicMock, extraction_result: ExtractionResult
    ) -> TripleService:
        svc = TripleService(client=mock_client, max_retries=0)
        svc._extractor.run = MagicMock(return_value=extraction_result)  # type: ignore[method-assign]
        return svc

    def test_run_returns_triples_and_result(
        self, mock_client: MagicMock, java_source: SourceMetadata
    ) -> None:
        e1, e2 = _entity("A"), _entity("B")
        er = _result(java_source, [e1, e2], [_rel(e1, e2, "USES")])
        svc = self._service_with_result(mock_client, er)
        triples, result = svc.run("some text", java_source)
        assert len(triples) == 1
        assert result is er

    def test_run_propagates_source_parser(
        self, mock_client: MagicMock, java_source: SourceMetadata
    ) -> None:
        er = _result(java_source, [], [])
        svc = self._service_with_result(mock_client, er)
        svc.run("text", java_source, source_parser="java_parser")
        svc._extractor.run.assert_called_once_with(  # type: ignore[union-attr]
            "text", java_source, "java_parser"
        )

    def test_run_returns_empty_triples_on_failed_extraction(
        self, mock_client: MagicMock, java_source: SourceMetadata
    ) -> None:
        er = ExtractionResult(
            source=java_source,
            status=ExtractionStatus.FAILED,
            errors=["LLM unavailable"],
        )
        svc = self._service_with_result(mock_client, er)
        triples, result = svc.run("text", java_source)
        assert triples == []
        assert result.status == ExtractionStatus.FAILED
