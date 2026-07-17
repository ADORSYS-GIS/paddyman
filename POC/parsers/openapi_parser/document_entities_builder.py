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
from openapi_parser.yaml_line_indexer import build_index as build_yaml_index
from openapi_parser.info_extractor import InfoExtractionError, extract_info_metadata
from openapi_parser.models import OpenApiMetadata
from openapi_parser.parameter_extractor import extract_parameters
from openapi_parser.ref_dereferencer import dereference_spec
from openapi_parser.schema_extractor import extract_schemas
from openapi_parser.api_entity_builder import build_api_entity
from openapi_parser.schema_composition_metadata import extract_schema_composition_map
from openapi_parser.security_extractor import extract_security_schemes
from shared.models import NormalizedDocument, SourceMetadata
from shared.id_factory import make_document_id
from uuid import UUID

logger = logging.getLogger(__name__)


def build_openapi_document_with_entities(
    root: Path,
    path: Path,
) -> tuple[NormalizedDocument, list[dict[str, Any]]]:
    """Build normalized document + entities for one OpenAPI YAML spec."""
    text = path.read_text(encoding="utf-8", errors="replace")
    relative_path = path.relative_to(root).as_posix()
    raw = _parse_raw_spec(text, path)
    # Build a light-weight YAML index of line ranges to attach provenance.
    yaml_index = build_yaml_index(text if isinstance(text, str) else "")
    metadata = _build_document_metadata(path, relative_path, raw)
    # Normalize path/file fields in parser metadata before creating SourceMetadata
    from shared.provenance import normalize_paths

    canonical_meta = normalize_paths(metadata, root=root)
    src = SourceMetadata.from_parser_metadata(canonical_meta).to_dict()
    # Parser-specific attributes live under `metadata` per the canonical
    # SourceMetadata contract; do not merge them into the top-level dict.
    doc = NormalizedDocument(
        document_id=make_document_id("openapi_parser", None, root, path),
        text=text,
        source_parser="openapi_parser",
        source_metadata=src,
        provenance={"path": str(path), "stage": "openapi_parser"},
    )
    if not isinstance(raw, dict):
        return doc, []

    entities = _extract_entities(raw, path)
    link_endpoint_payload_entities(entities, raw, str(path))
    # Attach per-entity provenance and source-line metadata when available.
    _attach_provenance_line_numbers(entities, yaml_index, str(path))

    # Normalize entity 'source' to the canonical document id so downstream
    # normalization and graph builders can reliably join entities -> documents.
    for ent in entities:
        old_source = ent.get("source")
        if old_source and old_source != doc.document_id:
            props = ent.get("properties")
            # If properties is a dict, store qualified_name there; otherwise
            # attach it at the entity top-level to avoid indexing into lists.
            if isinstance(props, dict):
                if "qualified_name" not in props and "qualified_name" not in ent:
                    props["qualified_name"] = old_source
            else:
                if "qualified_name" not in ent:
                    ent["qualified_name"] = old_source
        ent["source"] = doc.document_id

    return doc, entities


def _attach_provenance_line_numbers(entities: list[dict[str, Any]], yaml_index: dict[str, Any], file_path: str) -> None:
    """Attach best-effort `provenance` with `start_line`/`end_line` to entities.

    The function mutates entity dicts in-place. It uses the YAML index to
    map known components and paths to line ranges and places results under
    the top-level `provenance` key when available. This is intentionally
    best-effort: absent matches are left untouched.
    """
    from shared.provenance import ensure_provenance

    paths_idx = yaml_index.get("paths") or {}
    comps_idx = yaml_index.get("components") or {}

    for ent in entities:
        try:
            etype = ent.get("type")
            # Start with canonical provenance fields
            prov = ensure_provenance(ent.get("provenance") if isinstance(ent.get("provenance"), dict) else {}, file_path=file_path, stage="openapi_parser", parser="openapi_parser")

            start = None
            end = None
            if etype == "Operation":
                op_props = ent.get("properties") or {}
                method = op_props.get("method")
                path = op_props.get("path")
                if method and path:
                    rng = paths_idx.get((path, method.upper()))
                    if rng:
                        start, end = rng
            elif etype == "Endpoint":
                path = ent.get("path")
                method = ent.get("method")
                if path and method:
                    rng = paths_idx.get((path, method.upper()))
                    if rng:
                        start, end = rng
            else:
                name = ent.get("name")
                if name:
                    for comp_type, mapping in comps_idx.items():
                        if name in mapping:
                            rng = mapping.get(name)
                            if rng:
                                start, end = rng
                                break

            if start is not None and end is not None:
                try:
                    prov.setdefault("start_line", int(start))
                    prov.setdefault("end_line", int(end))
                except Exception:
                    prov.setdefault("start_line", start)
                    prov.setdefault("end_line", end)

            ent["provenance"] = prov
        except Exception:
            continue


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

    # API entity is available via builder but is not included in the
    # per-file `entities` array to keep the file-output focused on
    # endpoint-level entities. Relationship builders may still consume
    # API entities when they are present in a combined entity list.
    # (Do not append api_entity here.)
    def _to_ir(obj: Any) -> Any:
        """Convert a possible Pydantic model or dataclass to a plain IR dict.

        Also stringify UUIDs stored under the `id` key to make the
        resulting IR JSON-serializable for tests and file output.
        """
        try:
            if isinstance(obj, dict):
                res = obj
            elif hasattr(obj, "model_dump") and callable(obj.model_dump):
                res = obj.model_dump()
            elif hasattr(obj, "dict") and callable(obj.dict):
                res = obj.dict()
            else:
                return obj
        except Exception:
            return obj

        # Normalize UUIDs to strings for JSON serialization
        try:
            if isinstance(res.get("id"), UUID):
                res["id"] = str(res["id"])
        except Exception:
            pass
        return res

    # Ensure endpoint entities are plain dicts (IR) so linkers can mutate them
    for ep_meta in extract_endpoints(dereferenced, meta.title, str(path)):
        ep_ent = build_endpoint_entity(ep_meta)
        # Pydantic v1 -> dict(), v2 -> model_dump(); fall back to attribute check
        ep_dict = _to_ir(ep_ent)

        # Attach inline operation parameter metadata so relationship builders
        # can create HAS_PARAMETER relationships from operations/endpoints.
        params: list[dict[str, Any]] = []
        try:
            raw_params = getattr(ep_meta, "parameters", [])
        except Exception:
            raw_params = []
        if isinstance(raw_params, list):
            for p in raw_params:
                if not hasattr(p, "name"):
                    continue
                params.append({
                    "name": getattr(p, "name", None),
                    "location": getattr(p, "location", None),
                    "required": getattr(p, "required", False),
                    "description": getattr(p, "description", None),
                    "schema_type": getattr(p, "schema_type", None),
                    "schema_ref": getattr(p, "schema_ref", None),
                    "format": getattr(p, "format", None),
                    "deprecated": getattr(p, "deprecated", False),
                    "example": getattr(p, "example", None),
                })
        ep_dict["parameters"] = params
        entities.append(ep_dict)
        # Emit Parameter entities for inline/path-level parameters so they
        # become first-class entities available to relationship builders.
        try:
            raw_params = getattr(ep_meta, "parameters", [])
        except Exception:
            raw_params = []
        if isinstance(raw_params, list):
            for pmd in raw_params:
                try:
                    # Only create entities for parameters with a name
                    if not getattr(pmd, "name", None):
                        continue
                    param_ent = build_parameter_entity(pmd)
                    # Ensure inline/path-level parameters carry an accurate
                    # source_location (pointing to the path/method parameters
                    # list) so provenance attaching can map them to YAML lines.
                    try:
                        ep_path = getattr(ep_meta, "path", None)
                        ep_method = getattr(ep_meta, "method", None)
                        if ep_path and ep_method:
                            # method in EndpointMetadata is uppercase; normalize
                            param_ent["source_location"] = f"#/paths/{ep_path}/{ep_method.lower()}/parameters/{getattr(pmd, 'name')}"
                    except Exception:
                        pass
                    # Attach minimal provenance so later processing can
                    # enrich with start/end line numbers.
                    try:
                        from shared.provenance import ensure_provenance

                        param_ent.setdefault("provenance", {})
                        param_ent["provenance"] = ensure_provenance(param_ent.get("provenance"), file_path=str(path), stage="openapi_parser", parser="openapi_parser")
                    except Exception:
                        pass
                    entities.append(_to_ir(param_ent))
                except Exception:
                    continue
    for schema in extract_schemas(dereferenced, str(path)):
        schema_entities = [
            _to_ir(ent) for ent in build_schema_entities(schema)
        ]
        schema_composition = composition_map.get(schema.name)
        if schema_composition:
            _attach_schema_composition(schema_entities, schema.name, schema_composition)
        entities.extend(schema_entities)
    for param in extract_parameters(dereferenced, str(path)):
        try:
            entities.append(_to_ir(build_parameter_entity(param)))
        except Exception:
            continue

    for sec in extract_security_schemes(dereferenced, str(path)):
        try:
            entities.append(_to_ir(build_security_scheme_entity(sec)))
        except Exception:
            continue

    # Deduplicate Parameter entities by (name, in) keeping the last occurrence
    last_seen: dict[tuple[str | None, str | None], int] = {}
    for idx, ent in enumerate(entities):
        if ent.get("type") == "Parameter":
            key = (ent.get("name"), ent.get("in"))
            last_seen[key] = idx

    deduped: list[dict[str, Any]] = []
    for idx, ent in enumerate(entities):
        if ent.get("type") == "Parameter":
            key = (ent.get("name"), ent.get("in"))
            if last_seen.get(key) == idx:
                deduped.append(ent)
        else:
            deduped.append(ent)

    entities = deduped
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