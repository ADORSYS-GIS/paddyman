"""Unit tests for openapi_parser.parameter_extractor.

Covers:
- parameter extraction from components.parameters
- required vs optional parameters
- path, query, header parameter locations
- parameters with enum values
- parameters with format field
- missing components block
- missing parameters key
- empty parameters block
- non-dict parameter entry skipped
- multiple parameters extracted together
"""
from __future__ import annotations

from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Test fixtures (raw dicts — no YAML parsing needed, pure dict tests)
# ---------------------------------------------------------------------------

_PATH_PARAM: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "parameters": {
            "paymentService": {
                "name": "payment-service",
                "in": "path",
                "required": True,
                "description": "Payment service type",
                "schema": {
                    "type": "string",
                    "enum": ["payments", "bulk-payments", "periodic-payments"],
                },
            }
        }
    },
}

_QUERY_PARAM: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "parameters": {
            "limit": {
                "name": "limit",
                "in": "query",
                "required": False,
                "description": "Max items to return",
                "schema": {
                    "type": "integer",
                    "format": "int32",
                },
            }
        }
    },
}

_HEADER_PARAM: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "parameters": {
            "X-Request-ID": {
                "name": "X-Request-ID",
                "in": "header",
                "required": True,
                "description": "Unique request identifier",
                "schema": {
                    "type": "string",
                    "format": "uuid",
                },
            }
        }
    },
}

_MULTI_PARAMS: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "parameters": {
            "Foo": {
                "name": "foo",
                "in": "query",
                "schema": {"type": "string"},
            },
            "Bar": {
                "name": "bar",
                "in": "header",
                "schema": {"type": "integer"},
            },
            "Baz": {
                "name": "baz",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
            },
        }
    },
}

_DEPRECATED_PARAM: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "parameters": {
            "oldParam": {
                "name": "oldParam",
                "in": "query",
                "deprecated": True,
                "schema": {"type": "string"},
            }
        }
    },
}


class TestExtractParameters:
    def _import(self):
        from openapi_parser.parameter_extractor import extract_parameters
        return extract_parameters

    def test_path_parameter_extracted(self):
        extract = self._import()
        results = extract(_PATH_PARAM, "/test.yaml")

        assert len(results) == 1
        param = results[0]
        assert param.name == "paymentService"
        assert param.location == "path"
        assert param.required is True
        assert param.description == "Payment service type"
        assert param.schema_type == "string"
        assert len(param.enum_values) == 3
        assert param.enum_values == ["payments", "bulk-payments", "periodic-payments"]
        assert param.spec_source == "/test.yaml"

    def test_query_parameter_extracted(self):
        extract = self._import()
        results = extract(_QUERY_PARAM, "/test.yaml")

        assert len(results) == 1
        param = results[0]
        assert param.name == "limit"
        assert param.location == "query"
        assert param.required is False
        assert param.description == "Max items to return"
        assert param.schema_type == "integer"
        assert param.format == "int32"
        assert param.enum_values == []

    def test_header_parameter_extracted(self):
        extract = self._import()
        results = extract(_HEADER_PARAM, "/test.yaml")

        assert len(results) == 1
        param = results[0]
        assert param.name == "X-Request-ID"
        assert param.location == "header"
        assert param.required is True
        assert param.description == "Unique request identifier"
        assert param.schema_type == "string"
        assert param.format == "uuid"

    def test_multiple_parameters_extracted(self):
        extract = self._import()
        results = extract(_MULTI_PARAMS, "/test.yaml")

        assert len(results) == 3
        names = {p.name for p in results}
        assert names == {"Foo", "Bar", "Baz"}

        # Verify locations
        locations = {p.name: p.location for p in results}
        assert locations["Foo"] == "query"
        assert locations["Bar"] == "header"
        assert locations["Baz"] == "path"

    def test_deprecated_parameter_marked(self):
        extract = self._import()
        results = extract(_DEPRECATED_PARAM, "/test.yaml")

        assert len(results) == 1
        param = results[0]
        assert param.deprecated is True

    def test_missing_components_returns_empty(self):
        extract = self._import()
        spec = {"openapi": "3.0.1", "info": {"title": "T", "version": "1"}}
        results = extract(spec, "/test.yaml")

        assert results == []

    def test_missing_parameters_key_returns_empty(self):
        extract = self._import()
        spec = {
            "openapi": "3.0.1",
            "info": {"title": "T", "version": "1"},
            "components": {"schemas": {}},
        }
        results = extract(spec, "/test.yaml")

        assert results == []

    def test_empty_parameters_returns_empty(self):
        extract = self._import()
        spec = {
            "openapi": "3.0.1",
            "info": {"title": "T", "version": "1"},
            "components": {"parameters": {}},
        }
        results = extract(spec, "/test.yaml")

        assert results == []

    def test_non_dict_parameter_skipped(self):
        extract = self._import()
        spec = {
            "openapi": "3.0.1",
            "info": {"title": "T", "version": "1"},
            "components": {
                "parameters": {
                    "Valid": {
                        "name": "valid",
                        "in": "query",
                        "schema": {"type": "string"},
                    },
                    "Invalid": "not a dict",
                }
            },
        }
        results = extract(spec, "/test.yaml")

        assert len(results) == 1
        assert results[0].name == "Valid"

    def test_parameter_without_schema_has_none_type(self):
        extract = self._import()
        spec = {
            "openapi": "3.0.1",
            "info": {"title": "T", "version": "1"},
            "components": {
                "parameters": {
                    "NoSchema": {
                        "name": "noschema",
                        "in": "query",
                    }
                }
            },
        }
        results = extract(spec, "/test.yaml")

        assert len(results) == 1
        param = results[0]
        assert param.schema_type is None
        assert param.format is None

    def test_parameter_with_example(self):
        extract = self._import()
        spec = {
            "openapi": "3.0.1",
            "info": {"title": "T", "version": "1"},
            "components": {
                "parameters": {
                    "WithExample": {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "example": "abc123",
                    }
                }
            },
        }
        results = extract(spec, "/test.yaml")

        assert len(results) == 1
        param = results[0]
        assert param.example == "abc123"

    def test_enum_values_preserved(self):
        extract = self._import()
        results = extract(_PATH_PARAM, "/test.yaml")

        assert len(results) == 1
        param = results[0]
        assert isinstance(param.enum_values, list)
        assert len(param.enum_values) == 3
        assert "payments" in param.enum_values
        assert "bulk-payments" in param.enum_values
        assert "periodic-payments" in param.enum_values
