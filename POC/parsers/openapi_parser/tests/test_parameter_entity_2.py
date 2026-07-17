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

class TestBuildParameterEntity:
    """Test suite for build_parameter_entity function.

    Covers:
    - minimal parameter conversion
    - required vs optional parameters
    - path, query, header parameter locations
    - parameters with enum values
    - parameters with format field
    - deprecated parameters
    - parameters with examples
    - type field is "Parameter" (capitalized)
    - all optional fields default to appropriate values
    """

    def _import(self):
        from openapi_parser.entity_builder import build_parameter_entity
        return build_parameter_entity

    def test_header_parameter(self):
        from openapi_parser.models import ParameterMetadata

        build = self._import()
        param = ParameterMetadata(
            name="X-Request-ID",
            location="header",
            required=True,
            schema_type="string",
            format="uuid",
            description="Unique request identifier",
            spec_source="/specs/api.yaml",
        )
        entity = build(param)

        assert entity["type"] == "Parameter"
        assert entity["name"] == "X-Request-ID"
        assert entity["in"] == "header"
        assert entity["required"] is True
        assert entity["schema_type"] == "string"
        assert entity["format"] == "uuid"

    def test_deprecated_parameter(self):
        from openapi_parser.models import ParameterMetadata

        build = self._import()
        param = ParameterMetadata(
            name="oldParam",
            location="query",
            deprecated=True,
            spec_source="/specs/api.yaml",
        )
        entity = build(param)

        assert entity["type"] == "Parameter"
        assert entity["deprecated"] is True

    def test_parameter_with_example(self):
        from openapi_parser.models import ParameterMetadata

        build = self._import()
        param = ParameterMetadata(
            name="userId",
            location="path",
            required=True,
            schema_type="string",
            example="user123",
            spec_source="/specs/api.yaml",
        )
        entity = build(param)

        assert entity["type"] == "Parameter"
        assert entity["example"] == "user123"

    def test_type_field_capitalized(self):
        from openapi_parser.models import ParameterMetadata

        build = self._import()
        param = ParameterMetadata(
            name="test",
            location="query",
            spec_source="/specs/api.yaml",
        )
        entity = build(param)
        # Requirement: type field is "Parameter" (capital P) in entity
        assert entity["type"] == "Parameter"

    def test_cookie_parameter(self):
        from openapi_parser.models import ParameterMetadata

        build = self._import()
        param = ParameterMetadata(
            name="sessionId",
            location="cookie",
            required=False,
            schema_type="string",
            description="Session identifier",
            spec_source="/specs/api.yaml",
        )
        entity = build(param)

        assert entity["type"] == "Parameter"
        assert entity["name"] == "sessionId"
        assert entity["in"] == "cookie"
        assert entity["description"] == "Session identifier"

    def test_enum_values_empty_when_not_present(self):
        from openapi_parser.models import ParameterMetadata

        build = self._import()
        param = ParameterMetadata(
            name="noEnum",
            location="query",
            schema_type="string",
            spec_source="/specs/api.yaml",
        )
        entity = build(param)

        assert entity["enum_values"] == []


