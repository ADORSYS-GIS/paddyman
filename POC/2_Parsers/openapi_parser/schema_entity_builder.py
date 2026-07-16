"""Build normalized schema entity dicts with $ref tracking.

Pure transformation - converts SchemaMetadata records into flat entity
dictionaries with complete $ref resolution tracking metadata.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from openapi_parser.dto_entity_builder import build_dto_entities
from openapi_parser.enum_entity_builder import build_enum_entities
from openapi_parser.models import PropertyMetadata, SchemaMetadata


def build_schema_entity(schema: SchemaMetadata) -> dict[str, Any]:
    """Convert a SchemaMetadata record to a normalized entity dict.
    
    Includes $ref tracking metadata: is_reference, ref_path, external_refs,
    circular_refs, and ref_dereferenced status.
    """
    entity: dict[str, Any] = {
        "id": str(uuid4()),
        "type": "Schema",
        "name": schema.name,
        "schema_type": schema.schema_type,
        "description": schema.description,
        "source_file": schema.spec_source,
    }

    # Properties
    if schema.properties:
        entity["properties"] = [_property_to_dict(p) for p in schema.properties]
    else:
        entity["properties"] = []

    # Required field names
    entity["required"] = schema.required

    # Enum values
    if schema.enum_values:
        entity["enum_values"] = schema.enum_values
    else:
        entity["enum_values"] = []

    # Composition refs (allOf/oneOf/anyOf)
    if schema.refs:
        entity["refs"] = schema.refs
    else:
        entity["refs"] = []
    
    # $ref tracking metadata
    entity["is_reference"] = schema.is_reference
    entity["ref_path"] = schema.ref_path
    entity["external_refs"] = schema.external_refs
    entity["circular_refs"] = schema.circular_refs
    entity["ref_dereferenced"] = schema.ref_dereferenced

    return entity


def build_schema_entities(schema: SchemaMetadata) -> list[dict[str, Any]]:
    """Classify schema and build DTO/Enum/Schema entities.

    Rules:
    - schema with enum values -> Enum entity
    - object schema with properties -> DTO entity
    - otherwise -> generic Schema entity
    """
    if schema.enum_values:
        return build_enum_entities(schema)
    if schema.schema_type == "object" and schema.properties:
        return build_dto_entities(schema)
    return [build_schema_entity(schema)]


def _property_to_dict(prop: PropertyMetadata) -> dict[str, Any]:
    """Convert a PropertyMetadata record to a dict."""
    return {
        "name": prop.name,
        "type": prop.type,
        "ref": prop.ref,
        "description": prop.description,
        "required": prop.required,
        "enum_values": prop.enum_values,
        "format": prop.format,
    }
