"""Integration tests for API metadata entity and DEFINES relationships."""
from __future__ import annotations

import pytest

from openapi_parser.api_entity_builder import build_api_entity
from openapi_parser.api_relationship_builder import ApiRelationshipBuilder
from openapi_parser.relationship_builder import build_openapi_relationships


_SPEC_FILE = "/path/to/petstore.yaml"

_RAW_SPEC = {
    "openapi": "3.0.1",
    "info": {
        "title": "Petstore API",
        "version": "1.2.3",
        "description": "A sample API that uses a petstore.",
        "contact": {"name": "Dev Team", "email": "dev@petstore.com"},
        "license": {"name": "MIT"},
    },
}


def _make_entities(source_file: str = _SPEC_FILE) -> list[dict]:
    """Minimal entity set matching _RAW_SPEC for integration assertions."""
    api_entity = build_api_entity(_RAW_SPEC, source_file)
    assert api_entity is not None
    return [
        api_entity,
        {"id": "ep-1", "type": "Endpoint", "source_file": source_file,
         "path": "/pets", "method": "GET", "parameters": [],
         "request_body_ref": None, "request_body_match_key": None,
         "request_body_required": False, "response_refs": {},
         "response_match_keys": {}, "security_requirements": [], "api_title": "Petstore API"},
        {"id": "dto-1", "type": "DTO", "name": "Pet", "source_file": source_file,
         "properties": [], "required": [], "enum_values": [], "refs": [],
         "is_reference": False, "ref_path": None, "external_refs": [],
         "circular_refs": [], "ref_dereferenced": False},
        {"id": "schema-1", "type": "Schema", "name": "ErrorSchema", "source_file": source_file,
         "properties": [], "required": [], "enum_values": [], "refs": [],
         "is_reference": False, "ref_path": None, "external_refs": [],
         "circular_refs": [], "ref_dereferenced": False},
    ]


class TestApiEntityPerSpec:
    def test_one_api_entity_per_spec_file(self):
        entities = _make_entities()
        api_entities = [e for e in entities if e["type"] == "API"]
        assert len(api_entities) == 1

    def test_api_entity_title_matches_spec(self):
        entities = _make_entities()
        api = next(e for e in entities if e["type"] == "API")
        assert api["name"] == "Petstore API"
        assert api["version"] == "1.2.3"

    def test_api_entity_metadata_matches_spec_info(self):
        entities = _make_entities()
        api = next(e for e in entities if e["type"] == "API")
        assert api["contact_name"] == "Dev Team"
        assert api["contact_email"] == "dev@petstore.com"
        assert api["license_name"] == "MIT"
        assert api["openapi_version"] == "3.0.1"


class TestDefinesRelationships:
    def test_defines_covers_endpoint(self):
        entities = _make_entities()
        rels = ApiRelationshipBuilder().build(entities)
        api = next(e for e in entities if e["type"] == "API")
        defines = [r for r in rels if r["type"] == "DEFINES" and r["source_entity_id"] == api["id"]]
        target_ids = {r["target_entity_id"] for r in defines}
        assert "ep-1" in target_ids

    def test_defines_covers_dto(self):
        entities = _make_entities()
        rels = ApiRelationshipBuilder().build(entities)
        target_ids = {r["target_entity_id"] for r in rels}
        assert "dto-1" in target_ids

    def test_defines_covers_schema(self):
        entities = _make_entities()
        rels = ApiRelationshipBuilder().build(entities)
        target_ids = {r["target_entity_id"] for r in rels}
        assert "schema-1" in target_ids

    def test_defines_not_self_referential(self):
        """API entity must not DEFINE itself."""
        entities = _make_entities()
        api = next(e for e in entities if e["type"] == "API")
        rels = ApiRelationshipBuilder().build(entities)
        assert all(r["target_entity_id"] != api["id"] for r in rels)

    def test_defines_relationship_structure(self):
        entities = _make_entities()
        rels = ApiRelationshipBuilder().build(entities)
        for rel in rels:
            assert rel["type"] == "DEFINES"
            assert "id" in rel
            assert "source_entity_id" in rel
            assert "target_entity_id" in rel
            assert rel["properties"]["api_title"] == "Petstore API"
            assert rel["confidence"] == 1.0

    def test_multi_spec_isolation(self):
        """Entities from spec A must not be linked to API from spec B."""
        ents_a = _make_entities("/a.yaml")
        raw_b = {"openapi": "3.0.1", "info": {"title": "API B", "version": "1.0"}}
        api_b = build_api_entity(raw_b, "/b.yaml")
        ep_b = {"id": "ep-b", "type": "Endpoint", "source_file": "/b.yaml",
                "path": "/items", "method": "GET", "parameters": [],
                "request_body_ref": None, "request_body_match_key": None,
                "request_body_required": False, "response_refs": {},
                "response_match_keys": {}, "security_requirements": [], "api_title": "API B"}
        all_entities = ents_a + [api_b, ep_b]
        rels = ApiRelationshipBuilder().build(all_entities)
        api_a = next(e for e in ents_a if e["type"] == "API")
        for rel in rels:
            if rel["source_entity_id"] == api_a["id"]:
                assert rel["target_entity_id"] != "ep-b"
            if rel["source_entity_id"] == api_b["id"]:
                assert rel["target_entity_id"] not in {"ep-1", "dto-1", "schema-1"}


class TestDefinesViaRelationshipBuilder:
    def test_build_openapi_relationships_includes_defines(self):
        entities = _make_entities()
        rels = build_openapi_relationships(entities)
        defines_rels = [r for r in rels if r["type"] == "DEFINES"]
        assert len(defines_rels) >= 3  # endpoint + dto + schema
