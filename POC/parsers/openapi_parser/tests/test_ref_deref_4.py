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
    def test_list_traversal(self) -> None:
        """Refs inside lists are resolved."""
        spec = {
            "components": {
                "schemas": {
                    "Error": {"type": "object", "properties": {"message": {"type": "string"}}},
                }
            },
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            "400": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "oneOf": [
                                                {"$ref": "#/components/schemas/Error"},
                                                {"type": "string"},
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }

        resolver = InternalRefResolver(spec)
        resolved = resolver.resolve(spec)

        # Verify list item ref is resolved
        one_of = resolved["paths"]["/test"]["get"]["responses"]["400"]["content"][
            "application/json"
        ]["schema"]["oneOf"]
        assert one_of[0]["type"] == "object"
        assert one_of[0]["properties"]["message"]["type"] == "string"
        assert one_of[1]["type"] == "string"

    def test_dereference_spec_convenience_function(self) -> None:
        """dereference_spec convenience function works correctly."""
        spec = {
            "components": {
                "schemas": {
                    "Simple": {"type": "string"},
                }
            },
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/Simple"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }

        dereferenced = dereference_spec(spec)

        # Verify ref is resolved
        schema = dereferenced["paths"]["/test"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
        assert schema["type"] == "string"
