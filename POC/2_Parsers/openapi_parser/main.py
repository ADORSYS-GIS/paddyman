"""OpenAPI Parser pipeline orchestrator.

Runs the pipeline stages in order:

  1. Document loading     — ``SimpleDirectoryReader`` / ``GitLabReader``
                             ingests ``.yaml``/``.yml`` files with file-path
                             metadata attached (``RepoDocSync`` in L2 arch).
  2. Metadata extraction  — ``info`` block (title, version, servers)
  3. Endpoint extraction  — ``paths`` operations
  4. Schema extraction    — ``components.schemas``
  5. Reference resolution — ``$ref`` relationships

Entry point:

    from openapi_parser.main import run_pipeline
    summary = run_pipeline()            # reads path from shared.config
    summary = run_pipeline("/my/specs") # explicit path

Or as a script::

    python -m openapi_parser.main
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level stage overrides — monkeypatched by tests
# ---------------------------------------------------------------------------
load_documents_fn: Any = None    # readers.read_local  (Stage 1)
extract_endpoints_fn: Any = None
extract_schemas_fn: Any = None
resolve_refs_fn: Any = None
extract_security_schemes_fn: Any = None  # security_extractor.extract_security_schemes
extract_request_bodies_fn: Any = None  # request_response_extractor.extract_request_bodies
extract_responses_fn: Any = None       # request_response_extractor.extract_responses


def _prepare_import_paths() -> None:
    """Ensure ``2_Parsers/`` and ``POC/`` are on :data:`sys.path`."""
    script = Path(__file__).resolve()
    poc_root = script.parents[2]      # .../POC
    two_parsers = script.parents[1]   # .../POC/2_Parsers
    for p in (str(two_parsers), str(poc_root)):
        if p not in sys.path:
            sys.path.insert(0, p)


def _docs_to_raw_specs(docs: list[Any]) -> list[tuple[dict[str, Any], Any]]:
    """Convert LlamaIndex Documents to ``(raw_dict, OpenApiMetadata)`` pairs.

    Uses PyYAML's C-accelerated loader (:class:`yaml.CSafeLoader`) so that
    even large specs (500 KB+) parse in milliseconds.  Documents that cannot
    be parsed or lack required OpenAPI fields are skipped with a warning.
    """
    import yaml
    from yaml import CSafeLoader
    from openapi_parser.info_extractor import (
        InfoExtractionError,
        extract_info_metadata,
    )
    from openapi_parser.models import OpenApiMetadata

    results: list[tuple[dict[str, Any], Any]] = []
    for doc in docs:
        text: str = getattr(doc, "text", "") or ""
        spec_file: str = (getattr(doc, "metadata", {}) or {}).get("file_path") \
            or getattr(doc, "id_", None) or "<unknown>"
        try:
            raw: Any = yaml.load(text, Loader=CSafeLoader)
        except Exception as exc:
            logger.warning("Cannot parse YAML from %s: %s", spec_file, exc)
            continue
        if not isinstance(raw, dict):
            continue
        try:
            metadata_dict = extract_info_metadata(raw, spec_file)
            meta = OpenApiMetadata(spec_file=spec_file, **metadata_dict)
        except InfoExtractionError as exc:
            logger.warning("Skipping %s — %s", spec_file, exc)
            continue
        results.append((raw, meta))
    return results


def run_pipeline(source_dir: Path | str | None = None) -> dict[str, Any]:
    """Execute the complete OpenAPI Parser pipeline.

    Args:
        source_dir: Root directory containing OpenAPI YAML files.  When
            ``None`` the path is read from
            :data:`shared.config.settings.yaml_spec_dir`.

    Returns:
        Summary dictionary with counts for each pipeline stage and any errors
        encountered.
    """
    _prepare_import_paths()

    errors: list[str] = []

    # Resolve source directory ------------------------------------------------
    if source_dir is None:
        try:
            from shared.config import settings
            source_dir = settings.yaml_spec_dir
        except Exception as exc:
            msg = f"Cannot read yaml_spec_dir from shared.config: {exc}"
            logger.error(msg)
            return _empty_summary([msg])

    resolved = Path(source_dir)
    if not resolved.exists() or not resolved.is_dir():
        logger.warning("Source directory not found: %s", resolved)
        return _empty_summary([f"Source directory not found: {resolved}"])

    # Resolve stage callables (tests may monkeypatch module-level names) ------
    _load = load_documents_fn
    _endpoints = extract_endpoints_fn
    _schemas = extract_schemas_fn
    _refs = resolve_refs_fn
    _security = extract_security_schemes_fn
    _request_bodies = extract_request_bodies_fn
    _responses = extract_responses_fn

    if _load is None:
        from openapi_parser.readers import read_local as _rl
        _load = _rl
    if _endpoints is None:
        from openapi_parser.extractor import extract_endpoints as _ep_fn
        _endpoints = _ep_fn
    if _schemas is None:
        from openapi_parser.schema_extractor import extract_schemas as _sc_fn
        _schemas = _sc_fn
    if _refs is None:
        from openapi_parser.ref_resolver import resolve_refs as _rf_fn
        _refs = _rf_fn
    if _security is None:
        from openapi_parser.security_extractor import extract_security_schemes as _sec_fn
        _security = _sec_fn
    if _request_bodies is None:
        from openapi_parser.request_response_extractor import extract_request_bodies as _rb_fn
        _request_bodies = _rb_fn
    if _responses is None:
        from openapi_parser.request_response_extractor import extract_responses as _resp_fn
        _responses = _resp_fn

    # Stage 1: document loading (SimpleDirectoryReader / GitLabReader) --------
    try:
        docs: list[Any] = _load(resolved)
    except Exception as exc:
        logger.exception("Document loading failed: %s", exc)
        return _empty_summary([f"loading: {exc}"])

    # Stages 3–6: structural extraction from raw YAML dicts -------------------
    raw_specs = _docs_to_raw_specs(docs)

    all_endpoints: list[Any] = []
    all_schemas: list[Any] = []
    all_rels: list[Any] = []
    all_security_schemes: list[Any] = []
    all_request_bodies: list[Any] = []
    all_responses: list[Any] = []

    for raw, meta in raw_specs:
        spec = meta.spec_file

        # Stage 4: endpoint extraction ----------------------------------------
        try:
            eps = _endpoints(raw, meta.title, spec)
            all_endpoints.extend(eps)
        except Exception as exc:
            msg = f"endpoint extraction failed for {spec}: {exc}"
            logger.warning(msg)
            errors.append(msg)
            eps = []

        # Stage 5: schema extraction ------------------------------------------
        try:
            schs = _schemas(raw, spec)
            all_schemas.extend(schs)
        except Exception as exc:
            msg = f"schema extraction failed for {spec}: {exc}"
            logger.warning(msg)
            errors.append(msg)
            schs = []

        # Stage 6: reference resolution ---------------------------------------
        try:
            rels = _refs(raw, eps, schs, spec)
            all_rels.extend(rels)
        except Exception as exc:
            msg = f"ref resolution failed for {spec}: {exc}"
            logger.warning(msg)
            errors.append(msg)

        # Stage 7: security scheme extraction ---------------------------------
        try:
            sec = _security(raw, spec)
            all_security_schemes.extend(sec)
        except Exception as exc:
            msg = f"security scheme extraction failed for {spec}: {exc}"
            logger.warning(msg)
            errors.append(msg)

        # Stage 8: request body extraction ------------------------------------
        try:
            req_bodies = _request_bodies(raw, spec)
            all_request_bodies.extend(req_bodies)
        except Exception as exc:
            msg = f"request body extraction failed for {spec}: {exc}"
            logger.warning(msg)
            errors.append(msg)

        # Stage 9: response extraction ----------------------------------------
        try:
            resps = _responses(raw, spec)
            all_responses.extend(resps)
        except Exception as exc:
            msg = f"response extraction failed for {spec}: {exc}"
            logger.warning(msg)
            errors.append(msg)

    dtos = sum(1 for s in all_schemas if s.schema_type == "object")
    enums = sum(1 for s in all_schemas if s.enum_values)
    ep_schema_rels = sum(
        1 for r in all_rels if r.relationship in {"RETURNS", "ACCEPTS"}
    )

    summary = {
        "specs_loaded": len(raw_specs),
        "apis_discovered": len({m.title for _, m in raw_specs}),
        "endpoints_extracted": len(all_endpoints),
        "schemas_extracted": len(all_schemas),
        "dtos_extracted": dtos,
        "enums_extracted": enums,
        "refs_resolved": len(all_rels),
        "endpoint_schema_rels": ep_schema_rels,
        "security_schemes_extracted": len(all_security_schemes),
        "request_bodies_extracted": len(all_request_bodies),
        "responses_extracted": len(all_responses),
        "errors": errors,
    }

    logger.info(
        "OpenAPI pipeline complete — %d spec(s), %d endpoint(s), "
        "%d schema(s), %d relationship(s), %d request body(s), %d response(s)",
        summary["specs_loaded"],
        summary["endpoints_extracted"],
        summary["schemas_extracted"],
        summary["refs_resolved"],
        summary["request_bodies_extracted"],
        summary["responses_extracted"],
    )
    return summary


def _empty_summary(errors: list[str]) -> dict[str, Any]:
    return {
        "specs_loaded": 0,
        "apis_discovered": 0,
        "endpoints_extracted": 0,
        "schemas_extracted": 0,
        "dtos_extracted": 0,
        "enums_extracted": 0,
        "refs_resolved": 0,
        "endpoint_schema_rels": 0,
        "security_schemes_extracted": 0,
        "request_bodies_extracted": 0,
        "responses_extracted": 0,
        "errors": errors,
    }


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s — %(message)s")
    result = run_pipeline()
    from openapi_file_output import write_openapi_file_normalized_jsons

    output_paths = write_openapi_file_normalized_jsons({"openapi_parser": result})
    logger.info("OpenAPI parser spec outputs written to %s (%d files)", "DataSource/parsed_output/openapi_specs", len(output_paths))
    print(json.dumps(result, indent=2))
