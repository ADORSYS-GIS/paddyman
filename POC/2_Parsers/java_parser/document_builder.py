"""Helper functions for building Java parser documents."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from java_parser.java_ast.extractor import parse_and_extract
from shared.models import NormalizedDocument

logger = logging.getLogger(__name__)


def java_document(repo_root: Path, record: Any, module_label: str) -> NormalizedDocument:
    """Build a NormalizedDocument from a Java file record.
    
    Args:
        repo_root:    Repository root path.
        record:       JavaFileRecord instance.
        module_label: Module label.
        
    Returns:
        NormalizedDocument with metadata and text chunks.
    """
    path = repo_root / record.relative_path
    text = path.read_text(encoding="utf-8", errors="replace")
    metadata = {
        **record.to_dict(),
        "module": module_label,
        "file_path": str(path),
        "source_parser": "java_parser",
        "imports": java_imports(repo_root, record, module_label),
    }
    return NormalizedDocument(
        document_id=f"java_parser:{record.repository}:{module_label}:{record.relative_path}",
        text=text,
        source_parser="java_parser",
        source_metadata=metadata,
        provenance={"path": str(path), "stage": "java_parser", "module": module_label},
    )


def java_imports(repo_root: Path, record: Any, module_label: str) -> list[str]:
    """Extract import declarations from a Java file.
    
    Args:
        repo_root:    Repository root path.
        record:       JavaFileRecord instance.
        module_label: Module label.
        
    Returns:
        List of import statements.
    """
    path = repo_root / record.relative_path
    try:
        file_ast = parse_and_extract(
            path,
            repository=record.repository,
            module=module_label,
            repo_root=repo_root,
        )
    except Exception:  # noqa: BLE001
        logger.warning("Import extraction failed for %s", path, exc_info=True)
        return []
    return list(file_ast.imports)


def module_label(repository: str, module: str) -> str:
    """Compute module label from repository and module names."""
    return repository if module in {"", "."} else module


def safe_name(repository: str, module: str) -> str:
    """Generate a filesystem-safe name from repository and module."""
    raw = f"{repository}__{module}"
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in raw)
