"""Build Enum entities and enum value entities from OpenAPI schemas."""
from __future__ import annotations

from typing import Any
from uuid import NAMESPACE_URL, uuid5

from openapi_parser.models import SchemaMetadata


def build_enum_entities(schema: SchemaMetadata) -> list[dict[str, Any]]:
    """Build one Enum entity plus one EnumValue entity per enum literal."""
    enum_source = f"{schema.spec_source}:enum:{schema.name}"
    enum_id = str(uuid5(NAMESPACE_URL, f"openapi-enum:{enum_source}"))
    enum_values = list(schema.enum_values)
    value_links: list[dict[str, Any]] = []
    value_entities: list[dict[str, Any]] = []

    for position, value in enumerate(enum_values):
        value_source = f"{enum_source}:value:{position}:{value}"
        value_id = str(uuid5(NAMESPACE_URL, f"openapi-enum-value:{value_source}"))
        value_entities.append(
            {
                "id": value_id,
                "type": "EnumValue",
                "name": str(value),
                "source": f"openapi_parser:{value_source}",
                "properties": {
                    "value": value,
                    "position": position,
                    "base_type": schema.schema_type,
                },
            }
        )
        value_links.append(
            {
                "target_entity_id": value_id,
                "value": value,
                "position": position,
            }
        )

    enum_entity: dict[str, Any] = {
        "id": enum_id,
        "type": "Enum",
        "name": schema.name,
        "source": f"openapi_parser:{enum_source}",
        "schema_type": schema.schema_type,
        "description": schema.description,
        "source_file": schema.spec_source,
        "required": schema.required,
        "enum_values": enum_values,
        "refs": schema.refs,
        "is_reference": schema.is_reference,
        "ref_path": schema.ref_path,
        "external_refs": schema.external_refs,
        "circular_refs": schema.circular_refs,
        "ref_dereferenced": schema.ref_dereferenced,
        "properties": {
            "description": schema.description,
            "values": enum_values,
            "value_count": len(enum_values),
            "base_type": schema.schema_type,
            "source_file": schema.spec_source,
            "value_links": value_links,
        },
    }
    return [enum_entity, *value_entities]
