"""Unit tests for openapi_parser.schema_extractor (Chunk 3.3).

Covers:
- schema extraction from components.schemas
- object schema with properties and required fields
- enum schema
- inline property enum
- property types (primitive and $ref)
- property format field
- allOf / oneOf / anyOf $ref collection
- missing components block
- missing schemas key
- empty schemas block
- non-dict schema entry skipped
- invalid spec (no components)
- multiple schemas extracted together
"""
from __future__ import annotations

from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Test fixtures (raw dicts — no YAML parsing needed, pure dict tests)
# ---------------------------------------------------------------------------

_OBJECT_SCHEMA: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "schemas": {
            "PaymentRequest": {
                "type": "object",
                "description": "A payment request DTO.",
                "required": ["amount", "currency"],
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "Payment amount.",
                    },
                    "currency": {
                        "type": "string",
                        "description": "ISO 4217 currency code.",
                    },
                    "reference": {
                        "type": "string",
                        "description": "Optional reference.",
                    },
                },
            }
        }
    },
}

_ENUM_SCHEMA: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "schemas": {
            "TransactionStatus": {
                "type": "string",
                "description": "Status codes.",
                "enum": ["ACCP", "RJCT", "PDNG"],
            }
        }
    },
}

_REF_SCHEMA: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "schemas": {
            "AccountDetails": {
                "type": "object",
                "properties": {
                    "accountId": {"$ref": "#/components/schemas/accountId"},
                    "balance": {"type": "number"},
                },
            }
        }
    },
}

_ALLOF_SCHEMA: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "schemas": {
            "ExtendedAccount": {
                "allOf": [
                    {"$ref": "#/components/schemas/AccountDetails"},
                    {"$ref": "#/components/schemas/ExtraFields"},
                    {"type": "object", "properties": {"extra": {"type": "string"}}},
                ]
            }
        }
    },
}

_MULTI_SCHEMA: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "schemas": {
            "Foo": {"type": "string"},
            "Bar": {"type": "integer"},
            "Baz": {"type": "object", "properties": {}},
        }
    },
}

_INLINE_PROP_ENUM: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "schemas": {
            "OtpFormat": {
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "enum": ["characters", "integer"],
                    }
                },
            }
        }
    },
}

_FORMAT_PROP: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "T", "version": "1"},
    "components": {
        "schemas": {
            "ImageData": {
                "type": "object",
                "properties": {
                    "image": {"type": "string", "format": "byte"},
                },
            }
        }
    },
}


class TestExtractSchemas:
    def _import(self):
        from openapi_parser.schema_extractor import extract_schemas
        return extract_schemas

    # ── basic extraction ──────────────────────────────────────────────────

    def test_object_schema_extracted(self):
        schemas = self._import()(_OBJECT_SCHEMA, "/spec.yaml")
        assert len(schemas) == 1
        s = schemas[0]
        assert s.type == "schema"
        assert s.name == "PaymentRequest"
        assert s.spec_source == "/spec.yaml"
        assert s.schema_type == "object"
        assert s.description == "A payment request DTO."

    def test_multiple_schemas_extracted(self):
        schemas = self._import()(_MULTI_SCHEMA, "/spec.yaml")
        assert len(schemas) == 3
        names = {s.name for s in schemas}
        assert names == {"Foo", "Bar", "Baz"}

    # ── required fields ───────────────────────────────────────────────────

    def test_required_fields_captured(self):
        schemas = self._import()(_OBJECT_SCHEMA, "/spec.yaml")
        s = schemas[0]
        assert "amount" in s.required
        assert "currency" in s.required
        assert "reference" not in s.required

    def test_required_flag_on_property(self):
        schemas = self._import()(_OBJECT_SCHEMA, "/spec.yaml")
        props = {p.name: p for p in schemas[0].properties}
        assert props["amount"].required is True
        assert props["currency"].required is True
        assert props["reference"].required is False

    # ── properties ────────────────────────────────────────────────────────

    def test_properties_extracted(self):
        schemas = self._import()(_OBJECT_SCHEMA, "/spec.yaml")
        prop_names = {p.name for p in schemas[0].properties}
        assert prop_names == {"amount", "currency", "reference"}

    def test_property_type_captured(self):
        schemas = self._import()(_OBJECT_SCHEMA, "/spec.yaml")
        props = {p.name: p for p in schemas[0].properties}
        assert props["amount"].type == "number"
        assert props["currency"].type == "string"

    def test_property_description_captured(self):
        schemas = self._import()(_OBJECT_SCHEMA, "/spec.yaml")
        props = {p.name: p for p in schemas[0].properties}
        assert props["amount"].description == "Payment amount."

    def test_property_ref_captured(self):
        schemas = self._import()(_REF_SCHEMA, "/spec.yaml")
        props = {p.name: p for p in schemas[0].properties}
        assert props["accountId"].ref == "#/components/schemas/accountId"
        assert props["balance"].ref is None

    def test_property_format_captured(self):
        schemas = self._import()(_FORMAT_PROP, "/spec.yaml")
        props = {p.name: p for p in schemas[0].properties}
        assert props["image"].format == "byte"

    def test_inline_property_enum_captured(self):
        schemas = self._import()(_INLINE_PROP_ENUM, "/spec.yaml")
        props = {p.name: p for p in schemas[0].properties}
        assert props["format"].enum_values == ["characters", "integer"]

    # ── enum schema ───────────────────────────────────────────────────────

    def test_enum_schema_extracted(self):
        schemas = self._import()(_ENUM_SCHEMA, "/spec.yaml")
        s = schemas[0]
        assert s.name == "TransactionStatus"
        assert s.schema_type == "string"
        assert s.enum_values == ["ACCP", "RJCT", "PDNG"]

    def test_non_enum_schema_has_empty_enum_values(self):
        schemas = self._import()(_OBJECT_SCHEMA, "/spec.yaml")
        assert schemas[0].enum_values == []

    # ── $ref collection ───────────────────────────────────────────────────

    def test_allof_refs_collected(self):
        schemas = self._import()(_ALLOF_SCHEMA, "/spec.yaml")
        s = schemas[0]
        assert "#/components/schemas/AccountDetails" in s.refs
        assert "#/components/schemas/ExtraFields" in s.refs

    def test_allof_entry_without_ref_ignored(self):
        schemas = self._import()(_ALLOF_SCHEMA, "/spec.yaml")
        # The inline object entry (no $ref) should not appear in refs
        assert len(schemas[0].refs) == 2

    def test_plain_schema_has_empty_refs(self):
        schemas = self._import()(_OBJECT_SCHEMA, "/spec.yaml")
        assert schemas[0].refs == []

    # ── edge cases ────────────────────────────────────────────────────────

    def test_missing_components_returns_empty(self):
        raw = {"openapi": "3.0.1", "info": {"title": "T", "version": "1"}}
        assert self._import()(raw, "/spec.yaml") == []

    def test_missing_schemas_key_returns_empty(self):
        raw = {
            "openapi": "3.0.1",
            "info": {"title": "T", "version": "1"},
            "components": {"securitySchemes": {}},
        }
        assert self._import()(raw, "/spec.yaml") == []

    def test_empty_schemas_dict_returns_empty(self):
        raw = {
            "openapi": "3.0.1",
            "info": {"title": "T", "version": "1"},
            "components": {"schemas": {}},
        }
        assert self._import()(raw, "/spec.yaml") == []

    def test_non_dict_schema_entry_skipped(self):
        raw = {
            "openapi": "3.0.1",
            "info": {"title": "T", "version": "1"},
            "components": {
                "schemas": {
                    "Good": {"type": "string"},
                    "Bad": "this is not a dict",
                }
            },
        }
        schemas = self._import()(raw, "/spec.yaml")
        assert len(schemas) == 1
        assert schemas[0].name == "Good"

    def test_schema_without_type_still_extracted(self):
        raw = {
            "openapi": "3.0.1",
            "info": {"title": "T", "version": "1"},
            "components": {
                "schemas": {
                    "Ambiguous": {"description": "No type declared."},
                }
            },
        }
        schemas = self._import()(raw, "/spec.yaml")
        assert len(schemas) == 1
        assert schemas[0].schema_type is None
        assert schemas[0].description == "No type declared."

    def test_oneOf_refs_collected(self):
        raw = {
            "openapi": "3.0.1",
            "info": {"title": "T", "version": "1"},
            "components": {
                "schemas": {
                    "Union": {
                        "oneOf": [
                            {"$ref": "#/components/schemas/A"},
                            {"$ref": "#/components/schemas/B"},
                        ]
                    }
                }
            },
        }
        schemas = self._import()(raw, "/spec.yaml")
        assert "#/components/schemas/A" in schemas[0].refs
        assert "#/components/schemas/B" in schemas[0].refs
