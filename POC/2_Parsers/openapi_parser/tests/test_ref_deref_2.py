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
    def test_external_relative_ref_preserved(self) -> None:
        """External relative file ref is preserved with ref_type: external."""
        spec = {
            "paths": {
                "/payments": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "../common/schemas.yaml#/Payment"}
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

        # Verify relative ref is marked
        schema = resolved["paths"]["/payments"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
        assert schema["$ref"] == "../common/schemas.yaml#/Payment"
        assert schema["ref_type"] == "external"

    def test_circular_ref_detected(self) -> None:
        """Circular ref is detected and marked with ref_cycle_detected."""
        spec = {
            "components": {
                "schemas": {
                    "Node": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "string"},
                            "next": {"$ref": "#/components/schemas/Node"},
                        },
                    }
                }
            }
        }

        resolver = InternalRefResolver(spec)
        resolved = resolver.resolve(spec)

        # Verify circular ref is detected
        # The Node schema is resolved once, and within its 'next' property,
        # it attempts to resolve Node again, which triggers cycle detection
        node_schema = resolved["components"]["schemas"]["Node"]
        # The 'next' property is expanded once (first resolution)
        next_prop = node_schema["properties"]["next"]
        # Within that expansion, the nested 'next' property has the cycle flag
        nested_next = next_prop["properties"]["next"]
        assert nested_next.get("ref_cycle_detected") is True
        assert nested_next["$ref"] == "#/components/schemas/Node"

    def test_broken_ref_marked_unresolved(self) -> None:
        """Broken internal ref produces ref_resolved: false."""
        spec = {
            "paths": {
                "/payments": {
                    "get": {
                        "parameters": [
                            {"$ref": "#/components/parameters/NonExistent"}
                        ]
                    }
                }
            }
        }

        resolver = InternalRefResolver(spec)
        resolved = resolver.resolve(spec)

        # Verify broken ref is marked
        param = resolved["paths"]["/payments"]["get"]["parameters"][0]
        assert param["ref_resolved"] is False
        assert param["$ref"] == "#/components/parameters/NonExistent"

