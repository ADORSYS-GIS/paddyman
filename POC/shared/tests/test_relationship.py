"""Unit tests for shared.models.relationship."""
from __future__ import annotations

import dataclasses
from uuid import UUID, uuid4

import pytest

from shared.models.relationship import Relationship


def _make_rel(**kwargs) -> Relationship:
    defaults = dict(
        source_entity_id=uuid4(),
        target_entity_id=uuid4(),
        type="USES",
    )
    defaults.update(kwargs)
    return Relationship(**defaults)


class TestRelationshipCreation:
    def test_minimal_required_fields(self) -> None:
        src = uuid4()
        tgt = uuid4()
        rel = Relationship(source_entity_id=src, target_entity_id=tgt, type="USES")
        assert rel.source_entity_id == src
        assert rel.target_entity_id == tgt
        assert rel.type == "USES"
        assert isinstance(rel.id, UUID)
        assert rel.properties == {}
        assert rel.confidence == 1.0

    def test_explicit_id_is_preserved(self) -> None:
        explicit_id = uuid4()
        rel = _make_rel(id=explicit_id)
        assert rel.id == explicit_id

    def test_custom_confidence(self) -> None:
        rel = _make_rel(confidence=0.75)
        assert rel.confidence == 0.75

    def test_confidence_boundary_zero(self) -> None:
        rel = _make_rel(confidence=0.0)
        assert rel.confidence == 0.0

    def test_confidence_boundary_one(self) -> None:
        rel = _make_rel(confidence=1.0)
        assert rel.confidence == 1.0

    def test_each_instance_gets_unique_id(self) -> None:
        a = _make_rel()
        b = _make_rel()
        assert a.id != b.id


class TestRelationshipValidation:
    def test_empty_type_raises(self) -> None:
        with pytest.raises(ValueError, match="type"):
            _make_rel(type="")

    def test_whitespace_type_raises(self) -> None:
        with pytest.raises(ValueError, match="type"):
            _make_rel(type="  ")

    def test_confidence_below_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="confidence"):
            _make_rel(confidence=-0.01)

    def test_confidence_above_one_raises(self) -> None:
        with pytest.raises(ValueError, match="confidence"):
            _make_rel(confidence=1.01)


class TestRelationshipSerialization:
    def test_asdict_produces_expected_keys(self) -> None:
        rel = _make_rel()
        d = dataclasses.asdict(rel)
        assert set(d.keys()) == {
            "id", "source_entity_id", "target_entity_id",
            "type", "properties", "confidence",
        }
