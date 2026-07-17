"""Build Package entity dicts from Java AST file metadata."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any
from uuid import uuid4

from java_parser.java_ast.extractor import parse_and_extract
from java_parser.java_ast.models import JavaFileAst

logger = logging.getLogger(__name__)

_PACKAGE_RE = re.compile(r"[A-Za-z_][\w]*(\.[A-Za-z_][\w]*)*")


def package_entity_from_ast(file_ast: JavaFileAst) -> dict[str, Any] | None:
    """Convert a parsed file AST into a Package entity dict."""
    package_name = file_ast.package.strip()
    if not package_name or not _PACKAGE_RE.fullmatch(package_name):
        return None

    package_path = Path(file_ast.file_path).parent.as_posix()
    if package_path == ".":
        package_path = ""

    return {
        "type": "Package",
        "name": package_name,
        "qualified_name": package_name,
        "source": f"java_parser:{file_ast.repository}:{file_ast.module}:{package_name}",
        "repository": file_ast.repository,
        "module": file_ast.module,
        "file_path": package_path,
        "uuid": str(uuid4()),
    }


def package_entity_for_record(
    repo_root: Path,
    record: Any,
    module_label: str,
) -> dict[str, Any] | None:
    """Extract a Package entity for one Java file record."""
    path = repo_root / record.relative_path
    try:
        file_ast = parse_and_extract(
            path,
            repository=record.repository,
            module=module_label,
            repo_root=repo_root,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Package extraction failed for %s: %s", path, exc)
        return None

    return package_entity_from_ast(file_ast)


def unique_package_entities(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return package entities in first-seen order without duplicates."""
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for entity in entities:
        if entity.get("type") != "Package":
            continue
        key = entity.get("qualified_name") or entity.get("name")
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(entity)
    return unique