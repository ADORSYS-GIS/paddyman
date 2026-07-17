"""Unit tests for relationship vocabulary mapping rules."""
from __future__ import annotations

from relationships.rules import RelationshipTypeMapper, normalize_key


class TestNormalizeKey:
    def test_normalizes_lowercase(self) -> None:
        assert normalize_key("calls") == "CALLS"

    def test_normalizes_separator_variants(self) -> None:
        assert normalize_key("depends-on") == "DEPENDS_ON"
        assert normalize_key("depends on") == "DEPENDS_ON"

    def test_normalizes_camel_case(self) -> None:
        assert normalize_key("dependsOn") == "DEPENDS_ON"


class TestRelationshipTypeMapper:
    def test_required_mappings(self) -> None:
        mapper = RelationshipTypeMapper()
        assert mapper.normalize("CALLS") == "USES"
        assert mapper.normalize("USES") == "USES"
        assert mapper.normalize("DEPENDS_ON") == "DEPENDS_ON"
        assert mapper.normalize("REFERENCES") == "REFERENCES"
        assert mapper.normalize("RETURNS") == "EXPOSES"
        assert mapper.normalize("ACCEPTS") == "USES"
        assert mapper.normalize("IMPLEMENTS") == "IMPLEMENTS"
        assert mapper.normalize("EXTENDS") == "IMPLEMENTS"
        assert mapper.normalize("DOCUMENTS") == "DOCUMENTS"

    def test_unknown_type_defaults_to_references(self) -> None:
        assert RelationshipTypeMapper().normalize("mentions") == "REFERENCES"

    def test_custom_mapping_is_supported(self) -> None:
        mapper = RelationshipTypeMapper({"mentions": "documents"})
        assert mapper.normalize("MENTIONS") == "DOCUMENTS"