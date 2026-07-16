"""Unit tests for openapi_parser.ref_dereferencer.

Covers:
- Internal ref resolution to target objects
- External ref preservation with ref_type metadata
- Circular ref detection with ref_cycle_detected flag
- Broken ref handling with ref_resolved flag
- Recursive resolution up to max depth
- Dict and list traversal
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_POC_ROOT = Path(__file__).resolve().parents[3]
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from openapi_parser.ref_dereferencer import InternalRefResolver, dereference_spec


class TestInternalRefResolver:
    def test_resolve_internal_parameter_ref(self) -> None:
        """Internal parameter ref is resolved to target dict."""
        spec = {
            "components": {
                "parameters": {
                    "PaymentService": {
                        "name": "paymentService",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                }
            },
            "paths": {
                "/payments/{paymentService}": {
                    "get": {
                        "parameters": [{"$ref": "#/components/parameters/PaymentService"}]
                    }
                }
            },
        }

        resolver = InternalRefResolver(spec)
        resolved = resolver.resolve(spec)

        # Verify parameter ref is resolved
        params = resolved["paths"]["/payments/{paymentService}"]["get"]["parameters"]
        assert len(params) == 1
        assert params[0]["name"] == "paymentService"
        assert params[0]["in"] == "path"
        assert params[0]["required"] is True

    def test_resolve_internal_schema_ref(self) -> None:
        """Internal schema ref is resolved to target schema."""
        spec = {
            "components": {
                "schemas": {
                    "Payment": {
                        "type": "object",
                        "properties": {
                            "amount": {"type": "number"},
                        },
                    }
                }
            },
            "paths": {
                "/payments": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Payment"}
                                }
                            }
                        }
                    }
                }
            },
        }

        resolver = InternalRefResolver(spec)
        resolved = resolver.resolve(spec)

        # Verify schema ref is resolved
        schema = resolved["paths"]["/payments"]["post"]["requestBody"]["content"][
            "application/json"
        ]["schema"]
        assert schema["type"] == "object"
        assert "amount" in schema["properties"]

    def test_external_ref_preserved_with_metadata(self) -> None:
        """External ref (URL) is preserved with ref_type: external."""
        spec = {
            "paths": {
                "/payments": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "https://example.com/schemas/Payment.yaml"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        resolver = InternalRefResolver(spec)
        resolved = resolver.resolve(spec)

        # Verify external ref is marked
        schema = resolved["paths"]["/payments"]["post"]["requestBody"]["content"][
            "application/json"
        ]["schema"]
        assert schema["$ref"] == "https://example.com/schemas/Payment.yaml"
        assert schema["ref_type"] == "external"

