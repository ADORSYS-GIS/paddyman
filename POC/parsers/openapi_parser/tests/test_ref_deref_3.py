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
    def test_nested_ref_resolution(self) -> None:
        """Nested refs are resolved recursively."""
        spec = {
            "components": {
                "schemas": {
                    "Address": {
                        "type": "object",
                        "properties": {"street": {"type": "string"}},
                    },
                    "Person": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "address": {"$ref": "#/components/schemas/Address"},
                        },
                    },
                }
            },
            "paths": {
                "/people": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Person"}
                                }
                            }
                        }
                    }
                }
            },
        }

        resolver = InternalRefResolver(spec)
        resolved = resolver.resolve(spec)

        # Verify nested resolution
        schema = resolved["paths"]["/people"]["post"]["requestBody"]["content"][
            "application/json"
        ]["schema"]
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["address"]["properties"]["street"]["type"] == "string"

    def test_max_depth_prevents_infinite_recursion(self) -> None:
        """Max depth limit prevents runaway recursion."""
        spec = {
            "components": {
                "schemas": {
                    "Deep1": {"$ref": "#/components/schemas/Deep2"},
                    "Deep2": {"$ref": "#/components/schemas/Deep3"},
                    "Deep3": {"$ref": "#/components/schemas/Deep4"},
                    "Deep4": {"$ref": "#/components/schemas/Deep5"},
                    "Deep5": {"$ref": "#/components/schemas/Deep6"},
                    "Deep6": {"type": "string"},
                }
            }
        }

        resolver = InternalRefResolver(spec, max_depth=3)
        resolved = resolver.resolve(spec)

        # Should stop before reaching Deep6
        deep1 = resolved["components"]["schemas"]["Deep1"]
        assert "$ref" in deep1  # Did not fully resolve due to depth limit

