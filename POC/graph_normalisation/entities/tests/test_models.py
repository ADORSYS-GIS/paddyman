"""Unit tests for CanonicalEntity and EntitySource models."""
from __future__ import annotations

import pytest

from models import CanonicalEntity, EntitySource


class TestEntitySource:
    def test_valid_source(self) -> None:
        src = EntitySource(source_parser="java_parser", original_name="PaymentController")
        assert src.source_parser == "java_parser"
        assert src.original_name == "PaymentController"
        assert src.confidence == 1.0

    def test_empty_source_parser_raises(self) -> None:
        with pytest.raises(ValueError, match="source_parser"):
            EntitySource(source_parser="  ", original_name="Foo")

    def test_empty_original_name_raises(self) -> None:
        with pytest.raises(ValueError, match="original_name"):
            EntitySource(source_parser="java_parser", original_name="")

    def test_invalid_confidence_raises(self) -> None:
        with pytest.raises(ValueError, match="confidence"):
            EntitySource(
                source_parser="java_parser",
                original_name="Foo",
                confidence=1.5,
            )

    def test_negative_confidence_raises(self) -> None:
        with pytest.raises(ValueError, match="confidence"):
            EntitySource(
                source_parser="java_parser",
                original_name="Foo",
                confidence=-0.1,
            )

    def test_optional_fields_default_none(self) -> None:
        src = EntitySource(source_parser="spacy", original_name="Payment")
        assert src.repository is None
        assert src.module is None
        assert src.document is None
        assert src.file_path is None
        assert src.version_tag is None
        assert src.entity_ref is None


class TestCanonicalEntity:
    def test_valid_entity(self) -> None:
        entity = CanonicalEntity(id="PaymentInitiation", type="domain_entity")
        assert entity.id == "PaymentInitiation"
        assert entity.type == "domain_entity"
        assert entity.aliases == []
        assert entity.sources == []
        assert entity.confidence == 1.0

    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValueError, match="id"):
            CanonicalEntity(id="", type="domain_entity")

    def test_whitespace_id_raises(self) -> None:
        with pytest.raises(ValueError, match="id"):
            CanonicalEntity(id="   ", type="domain_entity")

    def test_empty_type_raises(self) -> None:
        with pytest.raises(ValueError, match="type"):
            CanonicalEntity(id="Foo", type="")

    def test_invalid_confidence_raises(self) -> None:
        with pytest.raises(ValueError, match="confidence"):
            CanonicalEntity(id="Foo", type="concept", confidence=2.0)

    def test_to_dict_structure(self) -> None:
        src = EntitySource(
            source_parser="java_parser",
            original_name="PaymentController",
            repository="xs2a",
            module="xs2a-impl",
            version_tag="v2",
            confidence=0.9,
        )
        entity = CanonicalEntity(
            id="PaymentInitiation",
            type="domain_entity",
            aliases=["PaymentController", "POST /payments"],
            sources=[src],
            confidence=0.9,
            properties={"extra": "value"},
        )
        d = entity.to_dict()
        assert d["id"] == "PaymentInitiation"
        assert d["type"] == "domain_entity"
        assert "PaymentController" in d["aliases"]
        assert len(d["sources"]) == 1
        assert d["sources"][0]["source_parser"] == "java_parser"
        assert d["sources"][0]["repository"] == "xs2a"
        assert "entity_id" in d["sources"][0]
        assert d["confidence"] == 0.9
        assert d["properties"] == {"extra": "value"}

    def test_to_dict_aliases_are_copy(self) -> None:
        entity = CanonicalEntity(
            id="Payment",
            type="concept",
            aliases=["A", "B"],
        )
        d = entity.to_dict()
        d["aliases"].append("C")
        assert len(entity.aliases) == 2

    def test_boundary_confidence_values(self) -> None:
        low = CanonicalEntity(id="Foo", type="concept", confidence=0.0)
        high = CanonicalEntity(id="Bar", type="concept", confidence=1.0)
        assert low.confidence == 0.0
        assert high.confidence == 1.0
