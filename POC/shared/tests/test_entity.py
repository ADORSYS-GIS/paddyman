"""Unit tests for shared.models.entity."""
from __future__ import annotations

import dataclasses
from uuid import UUID, uuid4

import pytest

from shared.models.entity import Entity


class TestEntityCreation:
    def test_minimal_required_fields(self) -> None:
        entity = Entity(type="Endpoint", name="GET /accounts", source="spec_v1")
        assert entity.type == "Endpoint"
        assert entity.name == "GET /accounts"
        assert entity.source == "spec_v1"
        assert isinstance(entity.id, UUID)
        assert entity.properties == {}

    def test_explicit_id_is_preserved(self) -> None:
        explicit_id = uuid4()
        entity = Entity(type="Schema", name="Account", source="doc", id=explicit_id)
        assert entity.id == explicit_id

    def test_properties_are_stored(self) -> None:
        props = {"version": "1.0", "deprecated": False}
        entity = Entity(type="Schema", name="Account", source="doc", properties=props)
        assert entity.properties == props

    def test_each_instance_gets_unique_id(self) -> None:
        a = Entity(type="T", name="A", source="s")
        b = Entity(type="T", name="A", source="s")
        assert a.id != b.id


class TestEntityValidation:
    def test_empty_type_raises(self) -> None:
        with pytest.raises(ValueError, match="type"):
            Entity(type="", name="name", source="src")

    def test_whitespace_type_raises(self) -> None:
        with pytest.raises(ValueError, match="type"):
            Entity(type="   ", name="name", source="src")

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name"):
            Entity(type="T", name="", source="src")

    def test_empty_source_raises(self) -> None:
        with pytest.raises(ValueError, match="source"):
            Entity(type="T", name="name", source="")


class TestEntitySerialization:
    def test_asdict_produces_expected_keys(self) -> None:
        entity = Entity(type="T", name="N", source="S")
        d = dataclasses.asdict(entity)
        assert set(d.keys()) == {"id", "type", "name", "source", "properties"}

    def test_asdict_id_is_uuid(self) -> None:
        entity = Entity(type="T", name="N", source="S")
        d = dataclasses.asdict(entity)
        # dataclasses.asdict converts UUID to UUID object
        assert isinstance(d["id"], UUID)
