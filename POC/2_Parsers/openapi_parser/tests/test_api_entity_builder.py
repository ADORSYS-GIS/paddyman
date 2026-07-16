"""Unit tests for api_entity_builder.build_api_entity."""
from __future__ import annotations

import pytest

from openapi_parser.api_entity_builder import build_api_entity


_MINIMAL_RAW = {
    "openapi": "3.0.1",
    "info": {"title": "Test API", "version": "1.0.0"},
}

_FULL_RAW = {
    "openapi": "3.0.1",
    "info": {
        "title": "Full API",
        "version": "2.5.0",
        "description": "A full description here.",
        "termsOfService": "https://example.com/tos",
        "contact": {
            "name": "Support Team",
            "email": "support@example.com",
            "url": "https://example.com/contact",
        },
        "license": {
            "name": "Apache 2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
        },
    },
}


class TestBuildApiEntityHappyPath:
    def test_minimal_spec_returns_entity(self):
        entity = build_api_entity(_MINIMAL_RAW, "/path/spec.yaml")
        assert entity is not None
        assert entity["type"] == "API"
        assert entity["name"] == "Test API"
        assert entity["title"] == "Test API"
        assert entity["version"] == "1.0.0"

    def test_id_is_string_uuid(self):
        entity = build_api_entity(_MINIMAL_RAW, "/path/spec.yaml")
        assert isinstance(entity["id"], str)
        assert len(entity["id"]) == 36  # UUID4 string length

    def test_source_file_captured(self):
        entity = build_api_entity(_MINIMAL_RAW, "/abs/path/to/spec.yaml")
        assert entity["source_file"] == "/abs/path/to/spec.yaml"

    def test_openapi_version_captured(self):
        entity = build_api_entity(_MINIMAL_RAW, "/path/spec.yaml")
        assert entity["openapi_version"] == "3.0.1"

    def test_contact_info_captured(self):
        entity = build_api_entity(_FULL_RAW, "/path/spec.yaml")
        assert entity["contact_name"] == "Support Team"
        assert entity["contact_email"] == "support@example.com"
        assert entity["contact_url"] == "https://example.com/contact"

    def test_license_info_captured(self):
        entity = build_api_entity(_FULL_RAW, "/path/spec.yaml")
        assert entity["license_name"] == "Apache 2.0"
        assert entity["license_url"] == "https://www.apache.org/licenses/LICENSE-2.0.html"

    def test_terms_of_service_captured(self):
        entity = build_api_entity(_FULL_RAW, "/path/spec.yaml")
        assert entity["terms_of_service"] == "https://example.com/tos"

    def test_description_captured(self):
        entity = build_api_entity(_FULL_RAW, "/path/spec.yaml")
        assert entity["description"] == "A full description here."


class TestBuildApiEntityOptionalFields:
    def test_optional_fields_none_when_absent(self):
        entity = build_api_entity(_MINIMAL_RAW, "/path/spec.yaml")
        assert entity["description"] is None
        assert entity["contact_name"] is None
        assert entity["contact_email"] is None
        assert entity["contact_url"] is None
        assert entity["license_name"] is None
        assert entity["license_url"] is None
        assert entity["terms_of_service"] is None

    def test_partial_contact_still_works(self):
        raw = {
            "openapi": "3.0.0",
            "info": {"title": "Partial", "version": "1.0", "contact": {"email": "a@b.com"}},
        }
        entity = build_api_entity(raw, "/path/spec.yaml")
        assert entity["contact_email"] == "a@b.com"
        assert entity["contact_name"] is None
        assert entity["contact_url"] is None


class TestBuildApiEntityInvalidInputs:
    def test_missing_info_block_returns_none(self):
        entity = build_api_entity({"openapi": "3.0.1"}, "/path/spec.yaml")
        assert entity is None

    def test_missing_title_returns_none(self):
        entity = build_api_entity(
            {"openapi": "3.0.1", "info": {"version": "1.0.0"}}, "/path/spec.yaml"
        )
        assert entity is None

    def test_missing_version_returns_none(self):
        entity = build_api_entity(
            {"openapi": "3.0.1", "info": {"title": "My API"}}, "/path/spec.yaml"
        )
        assert entity is None

    def test_empty_raw_returns_none(self):
        entity = build_api_entity({}, "/path/spec.yaml")
        assert entity is None


class TestBuildApiEntityDeterminism:
    def test_same_spec_produces_different_ids(self):
        """Each call produces a unique UUID4; dedup is downstream concern."""
        e1 = build_api_entity(_MINIMAL_RAW, "/path/spec.yaml")
        e2 = build_api_entity(_MINIMAL_RAW, "/path/spec.yaml")
        assert e1["id"] != e2["id"]

    def test_fields_are_stable_for_same_spec(self):
        e1 = build_api_entity(_FULL_RAW, "/path/spec.yaml")
        e2 = build_api_entity(_FULL_RAW, "/path/spec.yaml")
        for key in ("name", "title", "version", "contact_email", "license_name"):
            assert e1[key] == e2[key]
