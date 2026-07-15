"""Extract parameter entities and relationships from Java members."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from java_parser.members.member_builder import parse_and_extract_members
from java_parser.parameter_extraction_helpers import (
    extract_from_constructor,
    extract_from_method,
)

logger = logging.getLogger(__name__)


def parameter_entities_and_relationships_for_record(
    repo_root: Path,
    record: Any,
    document_id: str,
    module_label: str,
    imports: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract Parameter entities, annotation entities, and HAS_PARAMETER relationships.

    Args:
        repo_root:    Absolute path to the repository root directory.
        record:       :class:`~java_parser.discovery.models.JavaFileRecord`.
        document_id:  Document ID assigned to this file.
        module_label: Resolved module label.
        imports:      Import list for annotation resolution.

    Returns:
        Tuple of (all_entities, relationships) where all_entities includes both
        Parameter entities and Annotation entities for parameters.
    """
    path = repo_root / record.relative_path
    try:
        class_members_list = parse_and_extract_members(
            path,
            repository=record.repository,
            module=module_label,
            repo_root=repo_root,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Parameter extraction failed for %s: %s", path, exc)
        return ([], [])

    parameter_entities: list[dict[str, Any]] = []
    annotation_entities: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []

    for class_members in class_members_list:
        for method in class_members.methods:
            params, annots, rels = extract_from_method(method, document_id, imports)
            parameter_entities.extend(params)
            annotation_entities.extend(annots)
            relationships.extend(rels)

        for ctor in class_members.constructors:
            params, annots, rels = extract_from_constructor(ctor, document_id, imports)
            parameter_entities.extend(params)
            annotation_entities.extend(annots)
            relationships.extend(rels)

    all_entities = parameter_entities + annotation_entities
    return (all_entities, relationships)
