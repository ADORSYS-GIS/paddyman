"""Extract effective OpenAPI security requirements and OAuth2 scopes."""
from __future__ import annotations

from typing import Any
from uuid import NAMESPACE_URL, uuid5

_HTTP_METHODS: frozenset[str] = frozenset({"get", "post", "put", "patch", "delete", "options", "head"})


def extract_security_requirements(
    raw: dict[str, Any],
    spec_source: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract scope entities and effective endpoint/operation security requirements."""
    global_security = _normalize_security(raw.get("security"))
    paths = raw.get("paths")
    if not isinstance(paths, dict):
        return [], [], []

    scope_names: set[str] = set()
    endpoint_links: list[dict[str, Any]] = []
    operation_links: list[dict[str, Any]] = []

    for endpoint_path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        path_security = _normalize_security(path_item.get("security")) if "security" in path_item else None
        for method, operation in path_item.items():
            if method.lower() not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            op_security = _normalize_security(operation.get("security")) if "security" in operation else None
            effective = _effective_security(global_security, path_security, op_security)
            requirements = _flatten_requirements(effective)
            for req in requirements:
                for scope in req.get("scopes", []):
                    scope_names.add(scope)
            endpoint_links.append(
                {
                    "endpoint_path": str(endpoint_path),
                    "endpoint_method": str(method).upper(),
                    "security_requirements": requirements,
                }
            )
            operation_links.append(
                {
                    "operation_match_key": f"operation:{str(method).upper()}:{str(endpoint_path)}",
                    "security_requirements": requirements,
                }
            )

    return _build_scope_entities(spec_source, sorted(scope_names)), endpoint_links, operation_links


def _normalize_security(value: Any) -> list[dict[str, Any]] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _effective_security(
    global_security: list[dict[str, Any]] | None,
    path_security: list[dict[str, Any]] | None,
    op_security: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if op_security is not None:
        return op_security
    if path_security is not None:
        return path_security
    return global_security or []


def _flatten_requirements(security: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not security:
        return []
    has_optional_alternative = any(not item for item in security)
    required = not has_optional_alternative
    alternatives = len(security)

    flattened: list[dict[str, Any]] = []
    for req_index, requirement in enumerate(security):
        if not requirement:
            continue
        scheme_count = len(requirement)
        for scheme_index, (scheme_name, scopes) in enumerate(requirement.items()):
            flattened.append(
                {
                    "scheme_name": str(scheme_name),
                    "scopes": [str(scope) for scope in scopes] if isinstance(scopes, list) else [],
                    "required": required,
                    "optional": has_optional_alternative,
                    "logic": "AND" if scheme_count > 1 else "OR",
                    "alternatives": alternatives,
                    "requirement_index": req_index,
                    "scheme_index": scheme_index,
                }
            )
    return flattened


def _build_scope_entities(spec_source: str, scopes: list[str]) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    for scope_name in scopes:
        stable = f"{spec_source}:scope:{scope_name}"
        entities.append(
            {
                "id": str(uuid5(NAMESPACE_URL, f"openapi-scope:{stable}")),
                "type": "Scope",
                "name": scope_name,
                "source": f"openapi_parser:{stable}",
                "properties": {"scope_name": scope_name, "source_file": spec_source},
            }
        )
    return entities
