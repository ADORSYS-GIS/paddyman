"""Build a normalized API entity dict from an OpenAPI info block.

One API entity is produced per parsed specification file.
The entity captures all info-block metadata so APIs are queryable
as first-class nodes in the knowledge graph.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid5, NAMESPACE_URL

from shared.provenance import ensure_provenance
from shared.models import SourceMetadata

from openapi_parser.info_extractor import InfoExtractionError, extract_info_metadata

logger = logging.getLogger(__name__)


def build_api_entity(raw: dict[str, Any], source_file: str) -> dict[str, Any] | None:
    """Build an API entity from the spec info block.

    Args:
        raw:         Parsed (dereferenced) OpenAPI document.
        source_file: Absolute path to the source YAML file.

    Returns:
        Entity dict, or None if the info block is missing or invalid.
    """
    try:
        meta = extract_info_metadata(raw, source_file)
    except InfoExtractionError as exc:
        logger.warning("Cannot build API entity from %s: %s", source_file, exc)
        return None

    contact = meta.get("contact") or {}
    license_info = meta.get("license") or {}

    # Stable deterministic id based on source path
    stable_key = f"{source_file}"
    api_id = str(uuid5(NAMESPACE_URL, f"openapi-api:{stable_key}"))

    prov = ensure_provenance({}, file_path=source_file, stage="openapi_parser", parser="openapi_parser")

    source_meta = SourceMetadata.from_parser_metadata({
        "file_path": source_file,
        "source_parser": "openapi_parser",
        "api_title": meta.get("title"),
        "api_version": meta.get("version"),
    }).to_dict()

    return {
        "id": api_id,
        "type": "API",
        "name": meta["title"],
        "source_file": source_file,
        "title": meta["title"],
        "version": meta.get("version"),
        "description": meta.get("description"),
        "contact_name": contact.get("name") if isinstance(contact, dict) else None,
        "contact_email": contact.get("email") if isinstance(contact, dict) else None,
        "contact_url": contact.get("url") if isinstance(contact, dict) else None,
        "license_name": license_info.get("name") if isinstance(license_info, dict) else None,
        "license_url": license_info.get("url") if isinstance(license_info, dict) else None,
        "terms_of_service": meta.get("terms_of_service"),
        "openapi_version": meta.get("openapi_version"),
        "provenance": prov,
        "source_metadata": source_meta,
    }
