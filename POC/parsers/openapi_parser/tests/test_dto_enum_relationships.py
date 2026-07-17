"""Unit tests for DTO/Enum relationship builders."""
from __future__ import annotations

from openapi_parser.dto_enum_relationships import (
    dto_property_relationships,
    enum_value_relationships,
)


def test_builds_has_property_relationships() -> None:
    dto = {
        "id": "dto-1",
        "type": "DTO",
        "properties": {
            "property_links": [
                {
                    "target_entity_id": "schema-amount",
                    "property_name": "amount",
                    "required": True,
                    "nullable": False,
                },
                {
                    "target_entity_id": "schema-remittance",
                    "property_name": "remittance",
                    "required": False,
                    "nullable": False,
                },
            ]
        },
    }

    relationships = dto_property_relationships([dto])

    assert len(relationships) == 2
    assert all(r["type"] == "HAS_PROPERTY" for r in relationships)
    assert relationships[0]["source_entity_id"] == "dto-1"
    assert relationships[0]["target_entity_id"] == "schema-amount"
    assert relationships[0]["properties"]["required"] is True


def test_builds_has_enum_value_relationships() -> None:
    enum = {
        "id": "enum-1",
        "type": "Enum",
        "properties": {
            "value_links": [
                {"target_entity_id": "enum-v1", "value": "sepa", "position": 0},
                {"target_entity_id": "enum-v2", "value": "instant", "position": 1},
            ]
        },
    }

    relationships = enum_value_relationships([enum])

    assert len(relationships) == 2
    assert all(r["type"] == "HAS_ENUM_VALUE" for r in relationships)
    assert relationships[1]["source_entity_id"] == "enum-1"
    assert relationships[1]["target_entity_id"] == "enum-v2"
    assert relationships[1]["properties"]["value"] == "instant"
    assert relationships[1]["properties"]["position"] == 1
