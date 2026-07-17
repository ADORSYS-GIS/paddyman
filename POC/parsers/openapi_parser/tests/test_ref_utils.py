"""Unit tests for openapi_parser.ref_utils.

Covers:
- External ref detection
- Internal ref detection
- Recursive $ref collection from schemas
- SchemaRefInfo creation with metadata
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

from openapi_parser.ref_metadata import RefMetadata
from openapi_parser.ref_utils import (
    collect_refs_from_schema,
    create_schema_ref_info,
    is_external_ref,
    is_internal_ref,
)


class TestRefDetection:
    def test_is_internal_ref(self) -> None:
        """Internal refs start with #/."""
        assert is_internal_ref("#/components/schemas/Account")
        assert is_internal_ref("#/components/parameters/PaymentId")
        assert not is_internal_ref("./common.yaml#/components/schemas/Address")
        assert not is_internal_ref("https://example.com/spec.yaml")

    def test_is_external_ref(self) -> None:
        """External refs contain file path or URL before #."""
        assert is_external_ref("./common.yaml#/components/schemas/Address")
        assert is_external_ref("../shared/types.yaml#/definitions/User")
        assert is_external_ref("primitives.yaml#/components/schemas/Max35Text")
        assert is_external_ref("https://example.com/spec.yaml#/definitions/Error")
        assert not is_external_ref("#/components/schemas/Account")


class TestCollectRefsFromSchema:
    def test_collect_refs_from_simple_schema(self) -> None:
        """Collect refs from schema properties."""
        schema = {
            "type": "object",
            "properties": {
                "address": {"$ref": "#/components/schemas/Address"},
                "currency": {"$ref": "#/components/schemas/Currency"},
            },
        }
        refs = collect_refs_from_schema(schema)
        assert len(refs) == 2
        assert "#/components/schemas/Address" in refs
        assert "#/components/schemas/Currency" in refs

    def test_collect_refs_from_allof(self) -> None:
        """Collect refs from allOf composition."""
        schema = {
            "allOf": [
                {"$ref": "#/components/schemas/Base"},
                {"$ref": "#/components/schemas/Extension"},
            ]
        }
        refs = collect_refs_from_schema(schema)
        assert len(refs) == 2
        assert "#/components/schemas/Base" in refs
        assert "#/components/schemas/Extension" in refs

    def test_collect_refs_nested(self) -> None:
        """Collect refs from deeply nested schema."""
        schema = {
            "type": "object",
            "properties": {
                "account": {
                    "type": "object",
                    "properties": {
                        "owner": {"$ref": "#/components/schemas/Person"}
                    },
                },
                "payments": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/Payment"},
                },
            },
            "allOf": [{"$ref": "#/components/schemas/Auditable"}],
        }
        refs = collect_refs_from_schema(schema)
        assert len(refs) == 3
        assert "#/components/schemas/Person" in refs
        assert "#/components/schemas/Payment" in refs
        assert "#/components/schemas/Auditable" in refs

    def test_collect_refs_from_empty_schema(self) -> None:
        """Empty schema returns empty list."""
        refs = collect_refs_from_schema({})
        assert refs == []

    def test_collect_refs_from_primitives(self) -> None:
        """Primitives return empty list."""
        assert collect_refs_from_schema("string") == []
        assert collect_refs_from_schema(42) == []
        assert collect_refs_from_schema(None) == []


class TestCreateSchemaRefInfo:
    def test_create_ref_info_without_metadata(self) -> None:
        """Create ref info for schema without ref metadata."""
        schema = {
            "type": "object",
            "properties": {
                "address": {"$ref": "#/components/schemas/Address"}
            },
        }
        info = create_schema_ref_info(schema)
        
        assert not info.is_reference
        assert info.ref_path is None
        assert len(info.refs) == 1
        assert "#/components/schemas/Address" in info.refs
        assert info.dereferenced is True
        assert info.circular_refs == []

    def test_create_ref_info_with_external_refs(self) -> None:
        """External refs are identified separately."""
        schema = {
            "type": "object",
            "properties": {
                "local": {"$ref": "#/components/schemas/Local"},
                "external": {"$ref": "./common.yaml#/components/schemas/External"},
            },
        }
        info = create_schema_ref_info(schema)
        
        assert len(info.refs) == 2
        assert len(info.external_refs) == 1
        assert "./common.yaml#/components/schemas/External" in info.external_refs

    def test_create_ref_info_with_ref_metadata(self) -> None:
        """Schema that is itself a reference."""
        schema = {"type": "object"}
        ref_metadata = RefMetadata(
            ref_path="#/components/schemas/Base",
            dereferenced=True,
            is_external=False,
            circular=False,
        )
        info = create_schema_ref_info(schema, ref_metadata)
        
        assert info.is_reference
        assert info.ref_path == "#/components/schemas/Base"
        assert info.dereferenced is True

    def test_create_ref_info_with_circular_ref(self) -> None:
        """Circular reference is tracked."""
        schema = {"type": "object"}
        ref_metadata = RefMetadata(
            ref_path="#/components/schemas/Node",
            dereferenced=False,
            is_external=False,
            circular=True,
        )
        info = create_schema_ref_info(schema, ref_metadata)
        
        assert info.is_reference
        assert len(info.circular_refs) == 1
        assert "#/components/schemas/Node" in info.circular_refs
