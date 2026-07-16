"""Build relationship dicts for inclusion in NormalizedJson outputs.

This module orchestrates relationship extraction from Java source files and
delegates conversion to the relationship_converters module.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Iterable, List

from java_parser.relationships import (
    extract_relationships_from_source,
    RelationshipType,
)
from java_parser.di.extractor import extract_di_from_source
from java_parser.relationship_converters import (
    java_rel_to_dict,
    struct_rel_to_dict,
    di_rel_to_dict,
)

logger = logging.getLogger(__name__)


def build_module_relationship_dicts(
    repo_root: Path,
    records: Iterable[Any],
    module_label: str,
    inventory_records: Iterable[Any],
) -> List[dict]:
    """Return relationship dicts (CALLS, EXTENDS, IMPLEMENTS, INJECTS).

    Args:
        repo_root: Absolute path to the repository root.
        records: Iterable of JavaFileRecord-like objects for the current module.
        module_label: Module label used for provenance.
        inventory_records: All JavaFileRecord objects in the repository (used
            to heuristically resolve targets to modules).
    """
    # Build simple name → list of (fqname, module) mapping from inventory
    name_map: dict[str, list[tuple[str, str]]] = {}
    for rec in inventory_records:
        base = rec.file[:-5] if rec.file.endswith(".java") else rec.file
        fq = f"{rec.package}.{base}" if rec.package else base
        name_map.setdefault(base, []).append((fq, rec.module))

    out: List[dict] = []
    for record in records:
        path = repo_root / record.relative_path
        try:
            source = path.read_bytes()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Cannot read %s: %s", path, exc)
            continue

        # Structural relationships (EXTENDS / IMPLEMENTS / CALLS)
        try:
            rels = extract_relationships_from_source(
                source,
                file_path=record.relative_path,
                repository=record.repository,
                module=module_label,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Relationship extraction failed for %s: %s", path, exc)
            rels = []

        for rel in rels:
            if rel.relationship_type == RelationshipType.CALLS.value:
                out.append(java_rel_to_dict(rel))
            elif rel.relationship_type in (RelationshipType.EXTENDS.value, RelationshipType.IMPLEMENTS.value):
                out.append(struct_rel_to_dict(rel, name_map))

        # Dependency injection relationships
        try:
            di_rels = extract_di_from_source(
                source,
                file_path=record.relative_path,
                repository=record.repository,
                module=module_label,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("DI extraction failed for %s: %s", path, exc)
            di_rels = []

        for drel in di_rels:
            out.append(di_rel_to_dict(drel, name_map))

    return out

