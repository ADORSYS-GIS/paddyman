"""Unit tests for api_relationship_builder.ApiRelationshipBuilder."""
from __future__ import annotations

import pytest

from openapi_parser.api_relationship_builder import ApiRelationshipBuilder


def _api(source_file: str = "/spec.yaml", name: str = "My API") -> dict:
    return {"id": "api-id-1", "type": "API", "name": name, "source_file": source_file}


def _endpoint(source_file: str = "/spec.yaml") -> dict:
    return {"id": "ep-id-1", "type": "Endpoint", "source_file": source_file}


def _dto(source_file: str = "/spec.yaml") -> dict:
    return {"id": "dto-id-1", "type": "DTO", "source_file": source_file}


def _operation(source_file: str = "/spec.yaml") -> dict:
    """Operation stores source_file inside nested properties."""
    return {
        "id": "op-id-1",
        "type": "Operation",
        "name": "getStuff",
        "properties": {"source_file": source_file},
    }


class TestApiRelationshipBuilderHappyPath:
    def test_defines_endpoint(self):
        entities = [_api(), _endpoint()]
        rels = ApiRelationshipBuilder().build(entities)
        assert len(rels) == 1
        rel = rels[0]
        assert rel["type"] == "DEFINES"
        assert rel["source_entity_id"] == "api-id-1"
        assert rel["target_entity_id"] == "ep-id-1"
        assert rel["properties"]["entity_type"] == "Endpoint"
        assert rel["properties"]["api_title"] == "My API"

    def test_defines_dto(self):
        entities = [_api(), _dto()]
        rels = ApiRelationshipBuilder().build(entities)
        assert len(rels) == 1
        assert rels[0]["properties"]["entity_type"] == "DTO"

    def test_defines_operation_with_nested_source_file(self):
        entities = [_api(), _operation()]
        rels = ApiRelationshipBuilder().build(entities)
        assert len(rels) == 1
        assert rels[0]["properties"]["entity_type"] == "Operation"

    def test_multiple_entities_all_defined(self):
        entities = [
            _api(),
            _endpoint(),
            _dto(),
            {"id": "schema-id-1", "type": "Schema", "source_file": "/spec.yaml"},
            {"id": "sec-id-1", "type": "SecurityScheme", "source_file": "/spec.yaml"},
        ]
        rels = ApiRelationshipBuilder().build(entities)
        assert len(rels) == 4
        types = {r["properties"]["entity_type"] for r in rels}
        assert types == {"Endpoint", "DTO", "Schema", "SecurityScheme"}

    def test_relationship_has_uuid_id(self):
        entities = [_api(), _endpoint()]
        rels = ApiRelationshipBuilder().build(entities)
        assert isinstance(rels[0]["id"], str)
        assert len(rels[0]["id"]) == 36

    def test_confidence_is_1(self):
        entities = [_api(), _endpoint()]
        rels = ApiRelationshipBuilder().build(entities)
        assert rels[0]["confidence"] == 1.0


class TestApiRelationshipBuilderEdgeCases:
    def test_no_api_entity_returns_empty(self):
        entities = [_endpoint()]
        rels = ApiRelationshipBuilder().build(entities)
        assert rels == []

    def test_empty_entities_returns_empty(self):
        assert ApiRelationshipBuilder().build([]) == []

    def test_api_only_returns_empty(self):
        rels = ApiRelationshipBuilder().build([_api()])
        assert rels == []

    def test_entity_without_source_file_skipped(self):
        entities = [_api(), {"id": "ep-id-2", "type": "Endpoint"}]
        rels = ApiRelationshipBuilder().build(entities)
        assert rels == []

    def test_entity_without_id_skipped(self):
        entities = [_api(), {"type": "Endpoint", "source_file": "/spec.yaml"}]
        rels = ApiRelationshipBuilder().build(entities)
        assert rels == []

    def test_tag_entity_not_linked(self):
        entities = [
            _api(),
            {"id": "tag-id-1", "type": "Tag", "source_file": "/spec.yaml"},
        ]
        rels = ApiRelationshipBuilder().build(entities)
        assert rels == []

    def test_multi_spec_entities_matched_to_correct_api(self):
        api_a = {"id": "api-a", "type": "API", "name": "A", "source_file": "/a.yaml"}
        api_b = {"id": "api-b", "type": "API", "name": "B", "source_file": "/b.yaml"}
        ep_a = {"id": "ep-a", "type": "Endpoint", "source_file": "/a.yaml"}
        ep_b = {"id": "ep-b", "type": "Endpoint", "source_file": "/b.yaml"}
        rels = ApiRelationshipBuilder().build([api_a, api_b, ep_a, ep_b])
        assert len(rels) == 2
        by_target = {r["target_entity_id"]: r for r in rels}
        assert by_target["ep-a"]["source_entity_id"] == "api-a"
        assert by_target["ep-b"]["source_entity_id"] == "api-b"
