"""Unit tests for openapi_parser.ref_resolver (Chunk 3.4).

Covers:
- RETURNS relationship from direct response schema $ref
- RETURNS via intermediate $ref (response component → schema)
- ACCEPTS relationship from requestBody schema $ref
- ACCEPTS via nested oneOf $ref in requestBody
- REFERENCES from schema allOf refs
- REFERENCES from schema property refs
- multiple endpoints sharing the same schema
- unresolvable $ref produces no relationship
- empty endpoints / schemas produces empty list
- spec_source propagated correctly
- relationship fields (type, method, path, ref_path)
- no duplicate suppression — all refs produce records
"""
from __future__ import annotations

import pytest
from openapi_parser.models import EndpointMetadata, SchemaMetadata, PropertyMetadata


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ep(method: str, path: str, responses=None, request_body=None) -> EndpointMetadata:
    return EndpointMetadata(
        type="endpoint",
        method=method,
        path=path,
        api_title="Test API",
        spec_source="/spec.yaml",
        responses=responses or {},
        request_body=request_body,
    )


def _schema(name: str, refs=None, properties=None) -> SchemaMetadata:
    return SchemaMetadata(
        type="schema",
        name=name,
        spec_source="/spec.yaml",
        refs=refs or [],
        properties=properties or [],
    )


def _prop(name: str, ref: str | None = None) -> PropertyMetadata:
    return PropertyMetadata(name=name, ref=ref)


# ---------------------------------------------------------------------------
# RETURNS
# ---------------------------------------------------------------------------

class TestReturns:
    def _resolve(self, raw, endpoints, schemas=None):
        from openapi_parser.ref_resolver import resolve_refs
        return resolve_refs(raw, endpoints, schemas or [], "/spec.yaml")

    def test_direct_response_schema_ref(self):
        ep = _ep("GET", "/payments", responses={
            "200": {
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/PaymentList"}
                    }
                }
            }
        })
        rels = self._resolve({}, [ep])
        returns = [r for r in rels if r.relationship == "RETURNS"]
        assert len(returns) == 1
        assert returns[0].source == "GET /payments"
        assert returns[0].target == "PaymentList"
        assert returns[0].endpoint_method == "GET"
        assert returns[0].endpoint_path == "/payments"

    def test_returns_rel_type_field(self):
        ep = _ep("POST", "/items", responses={
            "201": {"content": {"application/json": {"schema": {
                "$ref": "#/components/schemas/Item"
            }}}}
        })
        rels = self._resolve({}, [ep])
        assert rels[0].type == "relationship"
        assert rels[0].relationship == "RETURNS"

    def test_returns_ref_path_stored(self):
        ep = _ep("GET", "/x", responses={
            "200": {"content": {"application/json": {"schema": {
                "$ref": "#/components/schemas/Foo"
            }}}}
        })
        rels = self._resolve({}, [ep])
        assert rels[0].ref_path == "#/components/schemas/Foo"

    def test_intermediate_response_ref_followed(self):
        """Response $ref points to #/components/responses/... which has schema ref."""
        raw = {
            "components": {
                "responses": {
                    "OK_200": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/PaymentInfo"}
                            }
                        }
                    }
                }
            }
        }
        ep = _ep("GET", "/payments", responses={
            "200": {"$ref": "#/components/responses/OK_200"}
        })
        rels = self._resolve(raw, [ep])
        returns = [r for r in rels if r.relationship == "RETURNS"]
        assert any(r.target == "PaymentInfo" for r in returns)

    def test_no_schema_ref_in_response_produces_no_returns(self):
        ep = _ep("GET", "/health", responses={"200": {"description": "OK"}})
        rels = self._resolve({}, [ep])
        returns = [r for r in rels if r.relationship == "RETURNS"]
        assert returns == []

    def test_multiple_response_codes_each_produce_relationship(self):
        ep = _ep("GET", "/x", responses={
            "200": {"content": {"application/json": {"schema": {
                "$ref": "#/components/schemas/Success"
            }}}},
            "404": {"content": {"application/json": {"schema": {
                "$ref": "#/components/schemas/Error"
            }}}},
        })
        rels = self._resolve({}, [ep])
        returns = [r for r in rels if r.relationship == "RETURNS"]
        targets = {r.target for r in returns}
        assert targets == {"Success", "Error"}

    def test_multiple_endpoints_same_schema(self):
        ep1 = _ep("GET", "/a", responses={"200": {"content": {"application/json": {
            "schema": {"$ref": "#/components/schemas/Common"}
        }}}})
        ep2 = _ep("POST", "/b", responses={"200": {"content": {"application/json": {
            "schema": {"$ref": "#/components/schemas/Common"}
        }}}})
        rels = self._resolve({}, [ep1, ep2])
        returns = [r for r in rels if r.relationship == "RETURNS"]
        assert len(returns) == 2
        sources = {r.source for r in returns}
        assert sources == {"GET /a", "POST /b"}

    def test_unresolvable_intermediate_ref_skipped(self):
        ep = _ep("GET", "/x", responses={
            "200": {"$ref": "#/components/responses/NonExistent"}
        })
        rels = self._resolve({}, [ep])
        returns = [r for r in rels if r.relationship == "RETURNS"]
        assert returns == []


# ---------------------------------------------------------------------------
# ACCEPTS
# ---------------------------------------------------------------------------

class TestAccepts:
    def _resolve(self, raw, endpoints, schemas=None):
        from openapi_parser.ref_resolver import resolve_refs
        return resolve_refs(raw, endpoints, schemas or [], "/spec.yaml")

    def test_direct_request_body_schema_ref(self):
        ep = _ep("POST", "/payments", request_body={
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/PaymentRequest"}
                }
            }
        })
        rels = self._resolve({}, [ep])
        accepts = [r for r in rels if r.relationship == "ACCEPTS"]
        assert len(accepts) == 1
        assert accepts[0].source == "POST /payments"
        assert accepts[0].target == "PaymentRequest"

    def test_nested_oneof_in_request_body(self):
        ep = _ep("PUT", "/auth", request_body={
            "content": {
                "application/json": {
                    "schema": {
                        "oneOf": [
                            {"$ref": "#/components/schemas/PinAuth"},
                            {"$ref": "#/components/schemas/OtpAuth"},
                        ]
                    }
                }
            }
        })
        rels = self._resolve({}, [ep])
        accepts = [r for r in rels if r.relationship == "ACCEPTS"]
        targets = {r.target for r in accepts}
        assert targets == {"PinAuth", "OtpAuth"}

    def test_no_request_body_produces_no_accepts(self):
        ep = _ep("GET", "/items")
        rels = self._resolve({}, [ep])
        accepts = [r for r in rels if r.relationship == "ACCEPTS"]
        assert accepts == []


# ---------------------------------------------------------------------------
# REFERENCES
# ---------------------------------------------------------------------------

class TestReferences:
    def _resolve(self, raw, schemas):
        from openapi_parser.ref_resolver import resolve_refs
        return resolve_refs(raw, [], schemas, "/spec.yaml")

    def test_allof_produces_references(self):
        schema = _schema("Extended", refs=[
            "#/components/schemas/Base",
            "#/components/schemas/Extra",
        ])
        rels = self._resolve({}, [schema])
        refs_rels = [r for r in rels if r.relationship == "REFERENCES"]
        targets = {r.target for r in refs_rels}
        assert targets == {"Base", "Extra"}
        for r in refs_rels:
            assert r.source == "Extended"

    def test_property_ref_produces_references(self):
        schema = _schema("Account", properties=[
            _prop("accountId", ref="#/components/schemas/AccountId"),
            _prop("balance"),  # no ref
        ])
        rels = self._resolve({}, [schema])
        refs_rels = [r for r in rels if r.relationship == "REFERENCES"]
        assert len(refs_rels) == 1
        assert refs_rels[0].target == "AccountId"
        assert refs_rels[0].source == "Account"

    def test_schema_with_no_refs_produces_nothing(self):
        schema = _schema("Simple")
        rels = self._resolve({}, [schema])
        assert rels == []

    def test_multiple_schemas_combined(self):
        s1 = _schema("A", refs=["#/components/schemas/B"])
        s2 = _schema("C", properties=[_prop("d", ref="#/components/schemas/D")])
        rels = self._resolve({}, [s1, s2])
        assert len(rels) == 2
        targets = {r.target for r in rels}
        assert targets == {"B", "D"}

    def test_spec_source_propagated(self):
        from openapi_parser.ref_resolver import resolve_refs
        schema = _schema("A", refs=["#/components/schemas/B"])
        rels = resolve_refs({}, [], [schema], "/custom/path.yaml")
        assert rels[0].spec_source == "/custom/path.yaml"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def _resolve(self, raw, endpoints=None, schemas=None):
        from openapi_parser.ref_resolver import resolve_refs
        return resolve_refs(raw, endpoints or [], schemas or [], "/spec.yaml")

    def test_empty_inputs_returns_empty(self):
        assert self._resolve({}) == []

    def test_non_schema_ref_ignored(self):
        """$ref to #/components/parameters/... should not produce a relationship."""
        ep = _ep("GET", "/x", responses={
            "200": {"$ref": "#/components/parameters/SomeParam"}
        })
        raw = {"components": {"parameters": {"SomeParam": {"name": "x", "in": "query"}}}}
        rels = self._resolve(raw, [ep])
        returns = [r for r in rels if r.relationship == "RETURNS"]
        assert returns == []

    def test_circular_ref_does_not_hang(self):
        """Circular $ref chains must terminate due to the visited-set guard."""
        raw = {
            "components": {
                "responses": {
                    "Loop": {"$ref": "#/components/responses/Loop"}
                }
            }
        }
        ep = _ep("GET", "/x", responses={"200": {"$ref": "#/components/responses/Loop"}})
        rels = self._resolve(raw, [ep])
        # Should complete without error; may or may not produce relationships
        assert isinstance(rels, list)

    def test_relationship_endpoint_fields_none_for_schema_rels(self):
        schema = _schema("A", refs=["#/components/schemas/B"])
        rels = self._resolve({}, schemas=[schema])
        r = rels[0]
        assert r.endpoint_method is None
        assert r.endpoint_path is None
