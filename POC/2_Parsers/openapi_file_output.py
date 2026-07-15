"""Write OpenAPI parser normalized output as per-spec JSON files."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import yaml
from yaml import CSafeLoader

_PARSERS_ROOT = Path(__file__).resolve().parent
_POC_ROOT = _PARSERS_ROOT.parent
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from normalized_json import write_normalized_json
from openapi_parser.entity_builder import (
    build_endpoint_entity,
    build_parameter_entity,
    build_schema_entity,
    build_security_scheme_entity,
)
from openapi_parser.extractor import extract_endpoints
from openapi_parser.info_extractor import InfoExtractionError, extract_info_metadata
from openapi_parser.loader import OpenApiLoadError
from openapi_parser.models import OpenApiMetadata
from openapi_parser.parameter_extractor import extract_parameters
from openapi_parser.ref_dereferencer import dereference_spec
from openapi_parser.relationship_builder import build_openapi_relationships
from openapi_parser.schema_extractor import extract_schemas
from openapi_parser.security_extractor import extract_security_schemes
from shared.config import settings
from shared.models import NormalizedDocument, NormalizedJson

logger = logging.getLogger(__name__)


def write_openapi_file_normalized_jsons(
    summaries: dict[str, Any] | None = None,
    source_dir: Path | None = None,
    output_dir: Path | None = None,
) -> list[Path]:
    """Persist OpenAPI parser output as one normalized JSON file per YAML spec."""
    root = source_dir or settings.yaml_spec_dir
    target_dir = output_dir or settings.parser_output_dir / "openapi_specs"
    target_dir.mkdir(parents=True, exist_ok=True)
    for old_file in target_dir.glob("*.json"):
        old_file.unlink()

    paths: list[Path] = []
    for spec_path in _spec_files(root):
        doc, entities = _openapi_document_with_entities(root, spec_path)
        
        # Build relationships between entities
        relationships = build_openapi_relationships(entities)
        logger.debug("Built %d relationships from %s", len(relationships), spec_path.name)
        
        bundle = NormalizedJson(
            documents=[doc],
            entities=entities,
            relationships=relationships,
            source_metadata=[doc.source_metadata],  # Use document's enriched metadata
            provenance={"stage": "openapi_parser", "parser": "openapi_parser", "path": str(spec_path)},
            version_metadata={"contract": "parser-json", "version": "1.0", "summaries": summaries or {}},
        )
        paths.append(write_normalized_json(bundle, target_dir / f"{_safe_spec_name(root, spec_path)}.json"))
    return paths


def _spec_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted({path for pattern in ("*.yaml", "*.yml") for path in root.rglob(pattern) if path.is_file()})


def _extract_info_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract OpenAPI info block metadata for source_metadata.
    
    Args:
        raw: Parsed OpenAPI YAML document (top-level mapping).
        
    Returns:
        Dictionary with api_title, api_version, api_description_summary, and servers.
        Returns None values for missing fields.
    """
    info_metadata: dict[str, Any] = {
        "api_title": None,
        "api_version": None,
        "api_description_summary": None,
        "servers": [],
    }
    
    # Extract info block
    info = raw.get("info")
    if isinstance(info, dict):
        info_metadata["api_title"] = info.get("title")
        info_metadata["api_version"] = info.get("version")
        
        # Truncate description to 200 characters
        description = info.get("description")
        if description:
            desc_str = str(description).strip()
            info_metadata["api_description_summary"] = desc_str[:200] if len(desc_str) > 200 else desc_str
    
    # Extract servers list
    servers = raw.get("servers")
    if isinstance(servers, list):
        info_metadata["servers"] = servers
    
    return info_metadata


def _openapi_document_with_entities(
    root: Path, path: Path
) -> tuple[NormalizedDocument, list[dict[str, Any]]]:
    """Build document and extract endpoint entities from an OpenAPI spec.

    Args:
        root: Root directory of the spec collection.
        path: Path to the individual YAML spec file.

    Returns:
        A tuple of (NormalizedDocument, list of endpoint entities).
        The document contains the complete specification text.
        Entities are structured endpoint records for graph construction.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    relative_path = path.relative_to(root).as_posix()
    
    # Initialize metadata with basic fields
    metadata: dict[str, Any] = {
        "file_path": str(path),
        "relative_path": relative_path,
        "source_parser": "openapi_parser",
        "api_title": None,
        "api_version": None,
        "api_description_summary": None,
        "servers": [],
    }
    
    # Parse YAML to extract info metadata
    raw: Any = None
    try:
        raw = yaml.load(text, Loader=CSafeLoader)
        if isinstance(raw, dict):
            # Extract info block metadata
            info_metadata = _extract_info_metadata(raw)
            metadata.update(info_metadata)
    except Exception as exc:
        logger.warning("Failed to parse YAML from %s: %s; info metadata will be null", path, exc)
    
    # Create the document with enriched metadata
    doc = NormalizedDocument(
        document_id=f"openapi_parser:{relative_path}",
        text=text,
        source_parser="openapi_parser",
        source_metadata=metadata,
        provenance={"path": str(path), "stage": "openapi_parser"},
    )

    # Extract structured endpoint entities
    entities: list[dict[str, Any]] = []
    
    # Skip entity extraction if YAML parsing failed or is not a dict
    if not isinstance(raw, dict):
        if raw is not None:
            logger.warning("Spec at %s is not a dict; skipping entity extraction", path)
        return doc, entities
    
    try:
        # Dereference internal $ref pointers before entity extraction
        dereferenced = dereference_spec(raw)

        # Extract metadata to get API title
        try:
            metadata_dict = extract_info_metadata(dereferenced, str(path))
            meta = OpenApiMetadata(spec_file=str(path), **metadata_dict)
            api_title = meta.title
        except InfoExtractionError as exc:
            logger.warning("Cannot extract metadata from %s: %s; skipping entity extraction", path, exc)
            return doc, entities

        # Extract endpoints
        endpoint_records = extract_endpoints(dereferenced, api_title, str(path))
        entities.extend([build_endpoint_entity(ep) for ep in endpoint_records])
        logger.debug("Extracted %d endpoint entities from %s", len(endpoint_records), relative_path)

        # Extract schemas
        schema_records = extract_schemas(dereferenced, str(path))
        entities.extend([build_schema_entity(s) for s in schema_records])
        logger.debug("Extracted %d schema entities from %s", len(schema_records), relative_path)

        # Extract parameters
        parameter_records = extract_parameters(dereferenced, str(path))
        entities.extend([build_parameter_entity(p) for p in parameter_records])
        logger.debug("Extracted %d parameter entities from %s", len(parameter_records), relative_path)

        # Extract security schemes
        security_scheme_records = extract_security_schemes(dereferenced, str(path))
        entities.extend([build_security_scheme_entity(s) for s in security_scheme_records])
        logger.debug("Extracted %d security scheme entities from %s", len(security_scheme_records), relative_path)

    except Exception as exc:
        logger.warning("Failed to extract entities from %s: %s", path, exc, exc_info=True)

    return doc, entities


def _openapi_document(root: Path, path: Path) -> NormalizedDocument:
    """Build a NormalizedDocument from an OpenAPI spec (legacy, entities not extracted)."""
    doc, _ = _openapi_document_with_entities(root, path)
    return doc


def _safe_spec_name(root: Path, path: Path) -> str:
    raw = path.relative_to(root).with_suffix("").as_posix()
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in raw)