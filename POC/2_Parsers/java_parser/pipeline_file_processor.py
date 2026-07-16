"""Per-file pipeline stage execution."""
from __future__ import annotations

import logging
from pathlib import Path

from java_parser.di.extractor import extract_di_relationships
from java_parser.discovery.models import JavaFileRecord
from java_parser.java_ast.extractor import extract_file_ast
from java_parser.java_ast.models import JavaDeclarationType
from java_parser.java_ast.parser import parse_file
from java_parser.members.member_builder import extract_file_members
from java_parser.pipeline_summary import PipelineSummary
from java_parser.relationships.extractor import extract_relationships
from java_parser.relationships.models import RelationshipType
from java_parser.spring.classifier import extract_spring_components

logger = logging.getLogger(__name__)


def process_file(record: JavaFileRecord, repo_root: Path) -> PipelineSummary:
    """Run all pipeline stages on a single Java file.

    Failures are caught per-stage so a problematic file does not abort
    the entire pipeline run.
    """
    s = PipelineSummary(java_files=1)
    abs_path = repo_root / record.relative_path

    try:
        root, _ = parse_file(abs_path)
        file_ast = extract_file_ast(
            root,
            file_path=record.relative_path,
            repository=record.repository,
            module=record.module,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Parse failed for %s: %s", record.relative_path, exc)
        s.errors += 1
        return s

    # Declaration counts
    for decl in file_ast.declarations:
        if decl.type == JavaDeclarationType.CLASS:
            s.classes += 1
        elif decl.type == JavaDeclarationType.INTERFACE:
            s.interfaces += 1
        elif decl.type == JavaDeclarationType.ENUM:
            s.enums += 1

    # Member extraction
    try:
        for cm in extract_file_members(
            root,
            package=file_ast.package,
            file_path=record.relative_path,
            repository=record.repository,
            module=record.module,
        ):
            s.methods += len(cm.methods)
            s.fields += len(cm.fields)
            s.constructors += len(cm.constructors)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Member extraction failed for %s: %s", record.relative_path, exc)
        s.errors += 1

    # Spring annotations
    try:
        s.spring_components += len(extract_spring_components(root, file_ast))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Spring extraction failed for %s: %s", record.relative_path, exc)
        s.errors += 1

    # Dependency injection
    try:
        s.di_relationships += len(extract_di_relationships(root, file_ast))
    except Exception as exc:  # noqa: BLE001
        logger.warning("DI extraction failed for %s: %s", record.relative_path, exc)
        s.errors += 1

    # Structural relationships
    try:
        for rel in extract_relationships(root, file_ast):
            if rel.relationship_type == RelationshipType.EXTENDS.value:
                s.inheritance_relationships += 1
            elif rel.relationship_type == RelationshipType.IMPLEMENTS.value:
                s.implementation_relationships += 1
            elif rel.relationship_type == RelationshipType.CALLS.value:
                s.call_relationships += 1
    except Exception as exc:  # noqa: BLE001
        logger.warning("Relationship extraction failed for %s: %s", record.relative_path, exc)
        s.errors += 1

    return s
