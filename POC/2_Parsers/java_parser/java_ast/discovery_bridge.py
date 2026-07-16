"""Integration layer: parse discovery results through the AST extractor.

Accepts :class:`~java_parser.discovery.models.JavaFileRecord` instances
produced by the Chunk 1.1 discovery phase and produces
:class:`~java_parser.ast.models.JavaFileAst` objects ready for downstream
extraction stages.
"""
from __future__ import annotations

import logging
from pathlib import Path

from java_parser.discovery.models import JavaFileRecord, RepositoryInventory

from .extractor import parse_and_extract
from .models import JavaFileAst

logger = logging.getLogger(__name__)


def parse_record(record: JavaFileRecord, repo_root: Path) -> JavaFileAst:
    """Parse a single :class:`JavaFileRecord` and return its AST metadata.

    Args:
        record:    File record produced by the discovery phase.
        repo_root: Absolute path to the owning repository root.

    Returns:
        :class:`JavaFileAst` with extracted structural information.
    """
    abs_path = repo_root / record.relative_path
    return parse_and_extract(
        abs_path,
        repository=record.repository,
        module=record.module,
        repo_root=repo_root,
    )


def parse_inventory(
    inventory: RepositoryInventory,
) -> list[JavaFileAst]:
    """Parse all Java files in a :class:`RepositoryInventory`.

    Args:
        inventory: Repository inventory produced by the discovery phase.

    Returns:
        List of :class:`JavaFileAst` objects, one per successfully parsed file.
        Files that cannot be read are included with ``has_errors=True``.
    """
    results: list[JavaFileAst] = []
    for record in inventory.files:
        try:
            ast = parse_record(record, inventory.root_path)
            results.append(ast)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Unexpected error parsing %s: %s", record.relative_path, exc
            )
    return results
