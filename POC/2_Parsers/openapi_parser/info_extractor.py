"""Extract comprehensive API-level metadata from OpenAPI info object.

Responsibilities:
- Extract all info block fields (title, version, description, contact, license)
- Extract terms of service URL
- Extract external documentation
- Extract custom extension fields (x-*)
- Truncate descriptions for summary display
- Handle missing fields gracefully

This module keeps loader.py focused on file discovery and YAML parsing.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class InfoExtractionError(Exception):
    """Raised when required info fields are missing or invalid."""


def extract_info_metadata(raw: dict[str, Any], spec_file: str) -> dict[str, Any]:
    """Extract comprehensive metadata from OpenAPI info object.

    Args:
        raw:       Parsed OpenAPI document (top-level mapping).
        spec_file: Absolute path to the source file (for error messages).

    Returns:
        Dictionary containing all extracted info metadata fields.

    Raises:
        InfoExtractionError: When required fields (info, title, version) are missing.
    """
    info = raw.get("info")
    if not isinstance(info, dict):
        raise InfoExtractionError(
            f"Missing or invalid 'info' block in {spec_file!r}"
        )

    # Required fields
    title = info.get("title")
    if not title or not str(title).strip():
        raise InfoExtractionError(f"Missing 'info.title' in {spec_file!r}")

    version = info.get("version")
    if not version or not str(version).strip():
        raise InfoExtractionError(f"Missing 'info.version' in {spec_file!r}")

    # Build metadata dictionary
    metadata: dict[str, Any] = {
        "title": str(title).strip(),
        "version": str(version).strip(),
    }

    # Optional description
    description = info.get("description")
    if description:
        desc_str = str(description).strip()
        metadata["description"] = desc_str
        metadata["description_summary"] = _truncate_description(desc_str, 200)

    # Terms of service
    tos = info.get("termsOfService")
    if tos:
        metadata["terms_of_service"] = str(tos).strip()

    # Contact information
    contact = info.get("contact")
    if isinstance(contact, dict):
        metadata["contact"] = {}
        if "name" in contact:
            metadata["contact"]["name"] = str(contact["name"]).strip()
        if "email" in contact:
            metadata["contact"]["email"] = str(contact["email"]).strip()
        if "url" in contact:
            metadata["contact"]["url"] = str(contact["url"]).strip()

    # License information
    license_info = info.get("license")
    if isinstance(license_info, dict):
        metadata["license"] = {}
        if "name" in license_info:
            metadata["license"]["name"] = str(license_info["name"]).strip()
        if "url" in license_info:
            metadata["license"]["url"] = str(license_info["url"]).strip()

    # External documentation
    external_docs = raw.get("externalDocs")
    if isinstance(external_docs, dict):
        metadata["external_docs"] = {}
        if "url" in external_docs:
            metadata["external_docs"]["url"] = str(external_docs["url"]).strip()
        if "description" in external_docs:
            metadata["external_docs"]["description"] = str(
                external_docs["description"]
            ).strip()

    # OpenAPI version
    openapi_version = raw.get("openapi") or raw.get("swagger")
    if openapi_version:
        metadata["openapi_version"] = str(openapi_version)

    # Servers list
    servers_raw = raw.get("servers")
    if isinstance(servers_raw, list):
        metadata["servers"] = [
            dict(s) for s in servers_raw if isinstance(s, dict)
        ]
    else:
        metadata["servers"] = []

    # Custom extensions (x-*)
    extensions = {k: v for k, v in info.items() if k.startswith("x-")}
    if extensions:
        metadata["extensions"] = extensions

    return metadata


def _truncate_description(text: str, max_length: int) -> str:
    """Truncate description text for summary display.

    Args:
        text:       Full description text.
        max_length: Maximum length of truncated text.

    Returns:
        Truncated text with ellipsis if needed.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."
