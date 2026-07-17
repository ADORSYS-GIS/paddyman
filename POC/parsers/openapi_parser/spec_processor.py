"""Processes a single OpenAPI specification file."""
from __future__ import annotations

import logging
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import yaml

# Use relative imports matching the current package layout.
from .api_entity_builder import build_api_entity as extract_api_entity
from .extractor import extract_endpoints as extract_endpoint_entities
from .operation_extractor import extract_operation_entities
from .schema_extractor import extract_schemas
from .parameter_extractor import extract_parameters as extract_parameter_entities
from .request_body_extractor import extract_request_body_entities
from .response_extractor import extract_response_entities
from .security_extractor import extract_security_schemes as extract_security_scheme_entities

log = logging.getLogger(__name__)


def process_spec(spec_path: Path) -> dict[str, Any] | None:
    """
    Parse a single OpenAPI specification file and extract all relevant entities.
    """
    log.info(f"Processing OpenAPI specification: {spec_path}")
    try:
        with spec_path.open("r") as f:
            raw_spec = yaml.safe_load(f)
    except (IOError, yaml.YAMLError) as e:
        log.error(f"Failed to read or parse specification file {spec_path}: {e}")
        return None

    spec_source = str(spec_path)
    # Helper to convert dataclass instances (and nested structures) to plain dicts/lists
    def _serialize(obj: Any) -> Any:
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, list):
            return [_serialize(i) for i in obj]
        if isinstance(obj, dict):
            return {k: _serialize(v) for k, v in obj.items()}
        return obj

    # API entity (may be None)
    api_entity = extract_api_entity(raw_spec, spec_source)
    api_serial = _serialize(api_entity) if api_entity is not None else None

    # Determine API title for endpoint extraction
    api_title = None
    if isinstance(api_serial, dict) and api_serial.get("title"):
        api_title = api_serial.get("title")
    else:
        info = raw_spec.get("info")
        api_title = info.get("title") if isinstance(info, dict) else ""

    # Operations and tags
    operations, tags, op_endpoint_links = extract_operation_entities(raw_spec, spec_source)

    # Reusable parameters from components (may return dataclass instances)
    parameters_raw = extract_parameter_entities(raw_spec, spec_source)
    parameters = _serialize(parameters_raw)
    param_endpoint_links: list[dict[str, Any]] = []
    param_operation_links: list[dict[str, Any]] = []

    # Endpoints (extractor returns dataclass EndpointMetadata objects)
    endpoints_raw = extract_endpoint_entities(raw_spec, api_title, spec_source)
    endpoints = _serialize(endpoints_raw)

    # Schemas, request bodies, responses and security schemes
    schemas = _serialize(extract_schemas(raw_spec, spec_source))
    request_bodies = _serialize(extract_request_body_entities(raw_spec, spec_source))
    responses = _serialize(extract_response_entities(raw_spec, spec_source))
    security_schemes = _serialize(extract_security_scheme_entities(raw_spec, spec_source))

    # Embed child lists into the API entity so the written file is a single
    # top-level API object with its related components attached.
    if isinstance(api_serial, dict):
        api_serial.setdefault("endpoints", endpoints)
        api_serial.setdefault("operations", _serialize(operations))
        api_serial.setdefault("tags", _serialize(tags))
        api_serial.setdefault("parameters", parameters)
        api_serial.setdefault("request_bodies", request_bodies)
        api_serial.setdefault("responses", responses)
        api_serial.setdefault("security_schemes", security_schemes)
        api_serial.setdefault("schemas", schemas)

    return {
        "source_file": spec_source,
        "api": api_serial,
        "endpoints": endpoints,
        "operations": _serialize(operations),
        "tags": _serialize(tags),
        "operation_endpoint_links": _serialize(op_endpoint_links),
        "parameters": parameters,
        "parameter_endpoint_links": param_endpoint_links,
        "parameter_operation_links": param_operation_links,
        "request_bodies": request_bodies,
        "responses": responses,
        "security_schemes": security_schemes,
        "schemas": schemas,
    }
