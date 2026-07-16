"""Build OpenAPI normalized documents and entities from a spec file."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from yaml import CSafeLoader

from openapi_parser.entity_builder import (
    build_endpoint_entity,
    build_parameter_entity,
    build_schema_entities,
    build_security_scheme_entity,
)
from openapi_parser.endpoint_payload_linker import link_endpoint_payload_entities
from openapi_parser.extractor import extract_endpoints
from openapi_parser.info_extractor import InfoExtractionError, extract_info_metadata
from openapi_parser.models import OpenApiMetadata
from openapi_parser.parameter_extractor import extract_parameters
from openapi_parser.ref_dereferencer import dereference_spec
from openapi_parser.schema_extractor import extract_schemas
from openapi_parser.api_entity_builder import build_api_entity
from openapi_parser.schema_composition_metadata import extract_schema_composition_map
from openapi_parser.security_extractor import extract_security_schemes
from shared.models import NormalizedDocument

logger = logging.getLogger(__name__)


def build_openapi_document_with_entities(
    root: Path,
    path: Path,
) -> tuple[NormalizedDocument, list[dict[str, Any]]]:
    """Build normalized document + entities for one OpenAPI YAML spec."""
    text = path.read_text(encoding="utf-8", errors="replace")
    relative_path = path.relative_to(root).as_posix()
    raw = _parse_raw_spec(text, path)
    metadata = _build_document_metadata(path, relative_path, raw)
    doc = NormalizedDocument(
        document_id=f"openapi_parser:{relative_path}",
        text=text,
        source_parser="openapi_parser",
        source_metadata=metadata,
        provenance={"path": str(path), "stage": "openapi_parser"},
    )
    if not isinstance(raw, dict):
        return doc, []

    entities = _extract_entities(raw, path)
    link_endpoint_payload_entities(entities, raw, str(path))
    return doc, entities


def _parse_raw_spec(text: str, path: Path) -> Any:
    try:
        return yaml.load(text, Loader=CSafeLoader)
    except Exception as exc:
        logger.warning("Failed to parse YAML from %s: %s", path, exc)
        return None


def _build_document_metadata(path: Path, relative_path: str, raw: Any) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "file_path": str(path),
        "relative_path": relative_path,
        "source_parser": "openapi_parser",
        "api_title": None,
        "api_version": None,
        "api_description_summary": None,
        "servers": [],
    }
    if isinstance(raw, dict):
        info = raw.get("info")
        if isinstance(info, dict):
            metadata["api_title"] = info.get("title")
            metadata["api_version"] = info.get("version")
            description = info.get("description")
            if description:
                text = str(description).strip()
                metadata["api_description_summary"] = text[:200] if len(text) > 200 else text
        servers = raw.get("servers")
        if isinstance(servers, list):
            metadata["servers"] = servers
    return metadata


def _extract_entities(raw: dict[str, Any], path: Path) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    composition_map = extract_schema_composition_map(raw)
    dereferenced = dereference_spec(raw)
    try:
        meta_dict = extract_info_metadata(dereferenced, str(path))
        meta = OpenApiMetadata(spec_file=str(path), **meta_dict)
    except InfoExtractionError as exc:
        logger.warning("Cannot extract metadata from %s: %s", path, exc)
        return entities

    api_entity = build_api_entity(dereferenced, str(path))
    if api_entity:
        entities.append(api_entity)
    entities.extend(build_endpoint_entity(ep) for ep in extract_endpoints(dereferenced, meta.title, str(path)))
    for schema in extract_schemas(dereferenced, str(path)):
        schema_entities = build_schema_entities(schema)
        schema_composition = composition_map.get(schema.name)
        if schema_composition:
            _attach_schema_composition(schema_entities, schema.name, schema_composition)
        entities.extend(schema_entities)
    entities.extend(build_parameter_entity(param) for param in extract_parameters(dereferenced, str(path)))
    entities.extend(build_security_scheme_entity(sec) for sec in extract_security_schemes(dereferenced, str(path)))
    return entities


def _attach_schema_composition(
    schema_entities: list[dict[str, Any]],
    schema_name: str,
    schema_composition: list[dict[str, Any]],
) -> None:
    for entity in schema_entities:
        if entity.get("name") == schema_name and entity.get("type") in {"Schema", "DTO", "Enum"}:
            entity["schema_composition"] = schema_composition
            return