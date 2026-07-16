"""Build DTO entities and property schema entities from OpenAPI schemas."""
from __future__ import annotations

from typing import Any
from uuid import NAMESPACE_URL, uuid5

from openapi_parser.models import SchemaMetadata


def build_dto_entities(schema: SchemaMetadata) -> list[dict[str, Any]]:
    """Build one DTO entity plus one property Schema entity per DTO field."""
    dto_source = f"{schema.spec_source}:dto:{schema.name}"
    dto_id = str(uuid5(NAMESPACE_URL, f"openapi-dto:{dto_source}"))
    required_fields = list(schema.required)
    property_links: list[dict[str, Any]] = []
    property_entities: list[dict[str, Any]] = []

    for position, prop in enumerate(schema.properties):
        prop_source = f"{schema.spec_source}:dto:{schema.name}:property:{prop.name}:{position}"
        prop_id = str(uuid5(NAMESPACE_URL, f"openapi-dto-property:{prop_source}"))
        property_entities.append(
            {
                "id": prop_id,
                "type": "Schema",
                "name": f"{schema.name}.{prop.name}",
                "schema_type": prop.type,
                "description": prop.description,
                "source_file": schema.spec_source,
                "properties": [],
                "required": [],
                "enum_values": prop.enum_values,
                "refs": [prop.ref] if prop.ref else [],
                "is_reference": bool(prop.ref),
                "ref_path": prop.ref,
                "external_refs": [],
                "circular_refs": [],
                "ref_dereferenced": not bool(prop.ref),
            }
        )
        property_links.append(
            {
                "target_entity_id": prop_id,
                "property_name": prop.name,
                "required": prop.required,
                "nullable": False,
            }
        )

    dto_entity: dict[str, Any] = {
        "id": dto_id,
        "type": "DTO",
        "name": schema.name,
        "source": f"openapi_parser:{dto_source}",
        "schema_type": schema.schema_type,
        "description": schema.description,
        "source_file": schema.spec_source,
        "required": required_fields,
        "enum_values": schema.enum_values,
        "refs": schema.refs,
        "is_reference": schema.is_reference,
        "ref_path": schema.ref_path,
        "external_refs": schema.external_refs,
        "circular_refs": schema.circular_refs,
        "ref_dereferenced": schema.ref_dereferenced,
        "properties": {
            "description": schema.description,
            "required_fields": required_fields,
            "property_count": len(schema.properties),
            "source_file": schema.spec_source,
            "ref_path": schema.ref_path,
            "property_links": property_links,
        },
    }
    return [dto_entity, *property_entities]
