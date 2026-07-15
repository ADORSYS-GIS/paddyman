"""Unit tests for shared.models.extraction."""
from __future__ import annotations

from uuid import uuid4

import pytest

from shared.models.entity import Entity
from shared.models.extraction import ExtractionResult, ExtractionStatus
from shared.models.relationship import Relationship
from shared.models.source import SourceMetadata, SourceType


def _make_source() -> SourceMetadata:
    return SourceMetadata(
        source_id="spec.pdf",
        source_type=SourceType.DOCUMENT,
        location="/data/spec.pdf",
    )


def _make_entity(name: str = "Account") -> Entity:
    return Entity(type="Schema", name=name, source="spec.pdf")


def _make_relationship(src: Entity, tgt: Entity) -> Relationship:
    return Relationship(
        source_entity_id=src.id,
        target_entity_id=tgt.id,
        type="REFERENCES",
    )


class TestExtractionResultCreation:
    def test_minimal_creation(self) -> None:
        result = ExtractionResult(source=_make_source())
        assert result.entities == []
        assert result.relationships == []
        assert result.status == ExtractionStatus.PENDING
        assert result.errors == []
        assert result.warnings == []
        assert result.metadata == {}

    def test_with_entities_and_relationships(self) -> None:
        e1 = _make_entity("Account")
        e2 = _make_entity("Transaction")
        rel = _make_relationship(e1, e2)
        result = ExtractionResult(
            source=_make_source(),
            entities=[e1, e2],
            relationships=[rel],
            status=ExtractionStatus.SUCCESS,
        )
        assert result.entity_count == 2
        assert result.relationship_count == 1
        assert result.status == ExtractionStatus.SUCCESS

    def test_error_recording(self) -> None:
        result = ExtractionResult(
            source=_make_source(),
            errors=["Parse failure on page 3"],
            status=ExtractionStatus.PARTIAL,
        )
        assert result.has_errors is True
        assert len(result.errors) == 1

    def test_no_errors_has_errors_is_false(self) -> None:
        result = ExtractionResult(source=_make_source())
        assert result.has_errors is False

    def test_warnings_stored(self) -> None:
        result = ExtractionResult(
            source=_make_source(),
            warnings=["Low confidence on entity X"],
        )
        assert len(result.warnings) == 1


class TestExtractionResultComposition:
    def test_mutable_lists_are_independent_across_instances(self) -> None:
        r1 = ExtractionResult(source=_make_source())
        r2 = ExtractionResult(source=_make_source())
        r1.entities.append(_make_entity())
        assert r2.entity_count == 0

    def test_all_statuses_accepted(self) -> None:
        for status in ExtractionStatus:
            result = ExtractionResult(source=_make_source(), status=status)
            assert result.status == status
