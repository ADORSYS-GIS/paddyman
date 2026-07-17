"""Reference relationship builder for markdown.

Creates REFERENCES, LINKS_TO, and NEXT_REFERENCE relationships for references.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from .relationship_utils import create_relationship, is_in_range
from .reference_url_utils import extract_anchor_from_url

logger = logging.getLogger(__name__)


def create_reference_relationships(
    reference_entities: list[dict[str, Any]],
    section_entities: list[dict[str, Any]],
    paragraph_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create all reference relationships (REFERENCES, LINKS_TO, NEXT_REFERENCE)."""
    relationships: list[dict[str, Any]] = []
    relationships.extend(_create_container_references(
        reference_entities, section_entities, paragraph_entities))
    relationships.extend(_create_anchor_links(reference_entities, section_entities))
    relationships.extend(_create_section_reference_links(reference_entities, section_entities))
    relationships.extend(_create_external_spec_links(reference_entities))
    relationships.extend(_create_sequential_references(reference_entities))
    return relationships


def _create_container_references(
    reference_entities: list[dict[str, Any]],
    section_entities: list[dict[str, Any]],
    paragraph_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create REFERENCES relationships from containers to references."""
    relationships: list[dict[str, Any]] = []

    for reference in reference_entities:
        ref_line = reference["properties"]["start_line"]

        for section in section_entities:
            if is_in_range(ref_line, section["properties"]["start_line"],
                          section["properties"]["end_line"]):
                relationships.append(create_relationship(
                    section["id"], reference["id"], "REFERENCES",
                    {"relationship_type": "section_to_reference"}))
                break

        for paragraph in paragraph_entities:
            if is_in_range(ref_line, paragraph["properties"]["start_line"],
                          paragraph["properties"]["end_line"]):
                relationships.append(create_relationship(
                    paragraph["id"], reference["id"], "REFERENCES",
                    {"relationship_type": "paragraph_to_reference"}))
                break

    return relationships


def _create_anchor_links(
    reference_entities: list[dict[str, Any]],
    section_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create LINKS_TO relationships from anchor references to target sections."""
    relationships: list[dict[str, Any]] = []
    section_anchors = {
        section["properties"].get("heading_anchor"): section["id"]
        for section in section_entities
        if section["properties"].get("heading_anchor")
    }

    for reference in reference_entities:
        target_url = reference["properties"].get("target_url", "")
        if target_url.startswith("#"):
            anchor = extract_anchor_from_url(target_url)
            if anchor and anchor in section_anchors:
                relationships.append(create_relationship(
                    reference["id"], section_anchors[anchor], "LINKS_TO",
                    {"relationship_type": "reference_to_section"}))

    return relationships


def _create_sequential_references(
    reference_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create NEXT_REFERENCE relationships for sequential ordering."""
    sorted_refs = sorted(reference_entities,
                        key=lambda r: r["properties"]["start_line"])
    return [
        create_relationship(
            sorted_refs[i]["id"], sorted_refs[i + 1]["id"],
            "NEXT_REFERENCE", {"relationship_type": "sequential"})
        for i in range(len(sorted_refs) - 1)
    ]


def _create_section_reference_links(
    reference_entities: list[dict[str, Any]],
    section_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create REFERENCES edges from section-style references to target sections."""
    relationships: list[dict[str, Any]] = []
    by_number: dict[str, str] = {}
    for section in section_entities:
        heading = str(section.get("properties", {}).get("heading_text", ""))
        match = re.match(r"\s*(\d+(?:\.\d+)*)\b", heading)
        if match:
            by_number[match.group(1)] = section["id"]

    for reference in reference_entities:
        props = reference.get("properties", {})
        if props.get("reference_type") != "section":
            continue
        target_section = str(props.get("target_section", ""))
        target_id = by_number.get(target_section)
        if target_id:
            relationships.append(create_relationship(
                reference["id"], target_id, "REFERENCES",
                {"relationship_type": "reference_to_section", "reference_type": "section"}))
    return relationships


def _create_external_spec_links(
    reference_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create REFERENCES_EXTERNAL edges from references to external spec keys."""
    relationships: list[dict[str, Any]] = []
    for reference in reference_entities:
        props = reference.get("properties", {})
        if props.get("reference_type") != "external_spec":
            continue
        spec = str(props.get("target_spec", "")).strip()
        if not spec:
            continue
        relationships.append(create_relationship(
            reference["id"], f"external_spec:{spec}", "REFERENCES_EXTERNAL",
            {"relationship_type": "reference_to_external_spec", "target_spec": spec}))
    return relationships


