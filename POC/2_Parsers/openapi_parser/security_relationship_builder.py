"""Build security and scope relationships for endpoints and operations."""
from __future__ import annotations

from typing import Any
from uuid import uuid4


class SecurityRelationshipBuilder:
    """Build REQUIRES_SECURITY and REQUIRES_SCOPE relationships."""

    def build(self, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        endpoints = [entity for entity in entities if entity.get("type") == "Endpoint"]
        operations = [entity for entity in entities if entity.get("type") == "Operation"]
        security_schemes = [entity for entity in entities if entity.get("type") == "SecurityScheme"]
        scopes = [entity for entity in entities if entity.get("type") == "Scope"]

        scheme_index = {entity.get("name"): entity.get("id") for entity in security_schemes if entity.get("name") and entity.get("id")}
        scope_index = {entity.get("name"): entity.get("id") for entity in scopes if entity.get("name") and entity.get("id")}

        relationships: list[dict[str, Any]] = []
        relationships.extend(self._source_relationships(endpoints, "endpoint", scheme_index, scope_index))
        relationships.extend(self._source_relationships(operations, "operation", scheme_index, scope_index))
        return relationships

    def _source_relationships(
        self,
        sources: list[dict[str, Any]],
        source_type: str,
        scheme_index: dict[str, str],
        scope_index: dict[str, str],
    ) -> list[dict[str, Any]]:
        relationships: list[dict[str, Any]] = []
        for source in sources:
            source_id = source.get("id")
            if not source_id:
                continue
            for req in _requirements_for_source(source):
                scheme = req.get("scheme_name")
                if not isinstance(scheme, str):
                    continue
                scheme_id = scheme_index.get(scheme)
                if scheme_id:
                    relationships.append(_security_relationship(source, source_type, source_id, scheme_id, req))
                for scope in req.get("scopes", []):
                    scope_id = scope_index.get(scope)
                    if scope_id:
                        relationships.append(_scope_relationship(source, source_type, source_id, scope_id, scheme, str(scope)))
        return relationships


def _requirements_for_source(source: dict[str, Any]) -> list[dict[str, Any]]:
    security_reqs = source.get("security_requirements")
    if isinstance(security_reqs, list):
        return [req for req in security_reqs if isinstance(req, dict)]

    legacy_security = source.get("security")
    if not isinstance(legacy_security, list):
        return []

    requirements: list[dict[str, Any]] = []
    for req_index, requirement in enumerate(legacy_security):
        if not isinstance(requirement, dict):
            continue
        for scheme_index, (scheme_name, scopes) in enumerate(requirement.items()):
            requirements.append(
                {
                    "scheme_name": str(scheme_name),
                    "scopes": [str(scope) for scope in scopes] if isinstance(scopes, list) else [],
                    "required": True,
                    "optional": False,
                    "logic": "AND" if len(requirement) > 1 else "OR",
                    "alternatives": len(legacy_security),
                    "requirement_index": req_index,
                    "scheme_index": scheme_index,
                }
            )
    return requirements


def _security_relationship(
    source: dict[str, Any],
    source_type: str,
    source_id: str,
    scheme_id: str,
    req: dict[str, Any],
) -> dict[str, Any]:
    props: dict[str, Any] = {
        "security_scheme": req.get("scheme_name"),
        "scopes": req.get("scopes", []),
        "required": bool(req.get("required", False)),
        "optional": bool(req.get("optional", False)),
        "logic": req.get("logic"),
        "alternatives": req.get("alternatives"),
        "requirement_index": req.get("requirement_index"),
        "scheme_index": req.get("scheme_index"),
    }
    if source_type == "endpoint":
        props["endpoint_path"] = source.get("path")
        props["endpoint_method"] = source.get("method")
    else:
        op_props = source.get("properties") if isinstance(source.get("properties"), dict) else {}
        props["operation_id"] = op_props.get("operation_id") or source.get("name")
    return {
        "id": str(uuid4()),
        "source_entity_id": source_id,
        "target_entity_id": scheme_id,
        "type": "REQUIRES_SECURITY",
        "properties": props,
        "confidence": 1.0,
    }


def _scope_relationship(
    source: dict[str, Any],
    source_type: str,
    source_id: str,
    scope_id: str,
    scheme_name: str,
    scope_name: str,
) -> dict[str, Any]:
    props: dict[str, Any] = {"scope_name": scope_name, "security_scheme": scheme_name}
    if source_type == "endpoint":
        props["endpoint_path"] = source.get("path")
        props["endpoint_method"] = source.get("method")
    else:
        op_props = source.get("properties") if isinstance(source.get("properties"), dict) else {}
        props["operation_id"] = op_props.get("operation_id") or source.get("name")
    return {
        "id": str(uuid4()),
        "source_entity_id": source_id,
        "target_entity_id": scope_id,
        "type": "REQUIRES_SCOPE",
        "properties": props,
        "confidence": 1.0,
    }
