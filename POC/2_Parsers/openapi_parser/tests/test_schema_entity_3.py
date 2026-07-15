"""Unit tests for openapi_parser.entity_builder.

Covers:
- converting EndpointMetadata to entity dict
- all fields present in output
- optional fields as None when absent
- parameters list conversion
- type field is "Endpoint" (capitalized)
"""
from __future__ import annotations

import pytest

class TestBuildSchemaEntity:
    """Test suite for build_schema_entity function.

    Covers:
    - minimal schema conversion
    - object schema with properties and required fields
    - enum schema with enum_values
    - schema with composition refs (allOf/oneOf/anyOf)
    - property with $ref
    - property with inline enum
    - property with format field
    - type field is "Schema" (capitalized)
    - all optional fields default to empty lists
    """

    def _import(self):
        from openapi_parser.entity_builder import build_schema_entity
        return build_schema_entity

    def test_property_with_format(self):
        from openapi_parser.models import PropertyMetadata, SchemaMetadata

        build = self._import()
        schema = SchemaMetadata(
            type="schema",
            name="ImageData",
            spec_source="/specs/api.yaml",
            schema_type="object",
            properties=[
                PropertyMetadata(
                    name="image",
                    type="string",
                    format="byte",
                    description="Base64 encoded image.",
                    required=True,
                )
            ],
            required=["image"],
        )
        entity = build(schema)

        assert len(entity["properties"]) == 1
        prop = entity["properties"][0]
        assert prop["name"] == "image"
        assert prop["type"] == "string"
        assert prop["format"] == "byte"
        assert prop["description"] == "Base64 encoded image."

    def test_type_field_capitalized(self):
        from openapi_parser.models import SchemaMetadata

        build = self._import()
        schema = SchemaMetadata(
            type="schema",
            name="TestSchema",
            spec_source="/specs/api.yaml",
            schema_type="object",
        )
        entity = build(schema)
        # Requirement: type field is "Schema" (capital S) in entity
        assert entity["type"] == "Schema"

    def test_schema_without_type(self):
        from openapi_parser.models import SchemaMetadata

        build = self._import()
        schema = SchemaMetadata(
            type="schema",
            name="AnyOfSchema",
            spec_source="/specs/api.yaml",
            schema_type=None,  # Composition schemas may not have explicit type
            refs=["#/components/schemas/A", "#/components/schemas/B"],
        )
        entity = build(schema)

        assert entity["type"] == "Schema"
        assert entity["name"] == "AnyOfSchema"
        assert entity["schema_type"] is None
        assert len(entity["refs"]) == 2


