"""Normalize parser outputs into bundle-level entity contracts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shared.id_factory import stable_uuid

PARSER_BUNDLE_FILENAME = "java_openapi_markdown_parser_output.json"


def collect_parser_bundle_artifacts(parser_output_dir: Path | None) -> dict[str, Any]:
    artifacts: dict[str, Any] = {"entities": [], "relationships": [], "method_calls": [], "parser_indices": {}}
    if not parser_output_dir or not parser_output_dir.exists():
        return artifacts
    for path in sorted(item for item in parser_output_dir.rglob("*.json") if item.name != PARSER_BUNDLE_FILENAME):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        entities = [item for item in payload.get("entities") or [] if isinstance(item, dict)]
        params = _parameter_index(entities)
        artifacts["entities"].extend(_normalize_entities(entities, params, payload, path.name))
        artifacts["relationships"].extend([item for item in payload.get("relationships") or [] if isinstance(item, dict)])
        artifacts["method_calls"].extend([item for item in payload.get("method_calls") or [] if isinstance(item, dict)])
        _merge_parser_indices(artifacts["parser_indices"], payload, path.name)
    return artifacts


def _normalize_entities(entities: list[dict[str, Any]], params: dict[tuple[str, str], list[dict[str, Any]]], payload: dict[str, Any], file_name: str) -> list[dict[str, Any]]:
    return [_normalize_entity(entity, params, payload, file_name) for entity in entities]


def _normalize_entity(entity: dict[str, Any], params: dict[tuple[str, str], list[dict[str, Any]]], payload: dict[str, Any], file_name: str) -> dict[str, Any]:
    entity_type = str(entity.get("type") or "Entity")
    source_document = str(entity.get("source") or file_name)
    qualified_name = _qualified_name(entity, entity_type)
    source_path = _source_path(entity, payload)
    return {
        "type": entity_type,
        "name": str(entity.get("name") or ""),
        "source": source_document,
        "id": str(entity.get("id") or entity.get("uuid") or _stable_entity_id(entity, entity_type, source_document, qualified_name, source_path)),
        "properties": _properties(entity, entity_type, qualified_name, source_document, source_path, params),
    }


def _properties(entity: dict[str, Any], entity_type: str, qualified_name: str, source_document: str, source_path: str, params: dict[tuple[str, str], list[dict[str, Any]]]) -> dict[str, Any]:
    annotations = [str(item.get("qualified_name") or item.get("name") or item) for item in entity.get("annotations") or [] if str(item.get("qualified_name") or item.get("name") or item)]
    modifiers = [*([str(entity.get("visibility"))] if str(entity.get("visibility") or "") not in {"", "package-private"} else []), *[value for key, value in (("is_static", "static"), ("is_final", "final"), ("is_abstract", "abstract")) if entity.get(key)]]
    props: dict[str, Any] = {
        "fully_qualified_name": qualified_name,
        "package": entity.get("package") or (qualified_name.rsplit(".", 1)[0] if "." in qualified_name else ""),
        "module": entity.get("module") or "",
        "repository": entity.get("repository") or "",
        "source_document": source_document,
        "source_path": source_path,
        "annotations": annotations,
        "modifiers": modifiers,
    }
    props.update(_specific_properties(entity, entity_type, qualified_name, params))
    return props


def _specific_properties(entity: dict[str, Any], entity_type: str, qualified_name: str, params: dict[tuple[str, str], list[dict[str, Any]]]) -> dict[str, Any]:
    if entity_type in {"Class", "Interface", "Enum"}:
        return {"extends": entity.get("extends"), "implements": list(entity.get("implements") or []), "visibility": entity.get("visibility"), "is_abstract": bool(entity.get("is_abstract"))}
    if entity_type == "Method":
        return {"return_type": entity.get("return_type"), "signature": _signature(entity, qualified_name, _parameters_for(entity, params))}
    if entity_type == "Constructor":
        return {"return_type": None, "signature": _signature(entity, qualified_name, _parameters_for(entity, params), constructor=True)}
    if entity_type == "Field":
        return {"type": entity.get("field_type") or entity.get("type"), "visibility": entity.get("visibility"), "is_static": bool(entity.get("is_static")), "is_final": bool(entity.get("is_final"))}
    if entity_type == "Parameter":
        return {"type": entity.get("parameter_type") or entity.get("type"), "position": entity.get("position", 0), "is_vararg": bool(entity.get("is_vararg")), "method_qualified_name": entity.get("method_qualified_name")}
    if entity_type == "Annotation":
        return {"attributes": dict(entity.get("attributes") or {}), "target_type": entity.get("target_type"), "target_name": entity.get("target_name")}
    if entity_type == "Import":
        return {"imported_name": entity.get("imported_name") or entity.get("name"), "is_static": bool(entity.get("is_static")), "is_wildcard": bool(entity.get("is_wildcard"))}
    return {}


def _stable_entity_id(entity: dict[str, Any], entity_type: str, source_document: str, qualified_name: str, source_path: str) -> str:
    if entity_type == "Method":
        return stable_uuid("Method", source_document, qualified_name, str(entity.get("return_type") or ""))
    if entity_type == "Constructor":
        return stable_uuid("Constructor", source_document, qualified_name)
    if entity_type == "Parameter":
        return stable_uuid("Parameter", source_document, str(entity.get("method_qualified_name") or ""), str(entity.get("name") or ""), str(entity.get("position", 0)))
    if entity_type == "Import":
        return stable_uuid("Import", source_document, str(entity.get("name") or ""), source_path)
    if entity_type == "Annotation":
        return stable_uuid("Annotation", source_document, qualified_name, str(entity.get("target_type") or ""), str(entity.get("target_name") or ""), str(entity.get("start_line") or ""))
    return stable_uuid(entity_type, source_document, qualified_name, source_path)


def _parameter_index(entities: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for entity in entities:
        if entity.get("type") != "Parameter":
            continue
        index.setdefault((str(entity.get("source") or ""), str(entity.get("method_qualified_name") or "")), []).append(entity)
    for items in index.values():
        items.sort(key=lambda item: (int(item.get("position", 0)), str(item.get("name") or "")))
    return index


def _parameters_for(entity: dict[str, Any], params: dict[tuple[str, str], list[dict[str, Any]]]) -> list[dict[str, Any]]:
    owner = str(entity.get("qualified_class") or entity.get("class") or "")
    method_name = ".<init>" if entity.get("type") == "Constructor" else f".{entity.get('name') or ''}"
    return [{"name": str(item.get("name") or ""), "type": str(item.get("parameter_type") or ""), "position": int(item.get("position", 0)), "is_vararg": bool(item.get("is_vararg"))} for item in params.get((str(entity.get("source") or ""), owner + method_name), [])]


def _signature(entity: dict[str, Any], qualified_name: str, parameters: list[dict[str, Any]], constructor: bool = False) -> str:
    parts = ", ".join("{} {}".format(item["type"], item["name"]).strip() for item in parameters)
    return f"{qualified_name}({parts})" if constructor else f"{str(entity.get('return_type') or 'void')} {qualified_name}({parts})"


def _qualified_name(entity: dict[str, Any], entity_type: str) -> str:
    if entity_type in {"Class", "Interface", "Enum"}:
        return str(entity.get("qualified_name") or entity.get("qualified_class") or entity.get("name") or "")
    if entity_type in {"Method", "Constructor", "Field"}:
        return f"{str(entity.get('qualified_class') or entity.get('class') or '')}.{str(entity.get('name') or '')}".rstrip(".")
    if entity_type == "Parameter":
        return f"{str(entity.get('method_qualified_name') or '')}:{str(entity.get('name') or '')}".rstrip(":")
    if entity_type == "Annotation":
        return str(entity.get("qualified_name") or entity.get("name") or "")
    return str(entity.get("name") or "")


def _source_path(entity: dict[str, Any], payload: dict[str, Any]) -> str:
    # Prefer explicit location.path when available (added by parsers)
    if isinstance(entity.get("location"), dict) and entity.get("location").get("path"):
        return str(entity.get("location").get("path"))
    if entity.get("file_path"):
        return str(entity.get("file_path"))
    for document in payload.get("documents") or []:
        provenance = document.get("provenance") if isinstance(document, dict) else {}
        if isinstance(provenance, dict) and provenance.get("path"):
            return str(provenance.get("path"))
    return ""


def _merge_parser_indices(target: dict[str, dict[str, Any]], payload: dict[str, Any], file_name: str) -> None:
    for index_name, index_value in (payload.get("parser_indices") or {}).items():
        target.setdefault(index_name, {})[file_name] = index_value
    if payload.get("method_calls"):
        target.setdefault("method_calls", {})[file_name] = payload.get("method_calls")
