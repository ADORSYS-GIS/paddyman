"""Helper functions for building Java parser documents."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from java_parser.java_ast.extractor import parse_and_extract
from shared.models import NormalizedDocument, SourceMetadata
from shared.id_factory import make_document_id

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
    parser_meta = {
        **record.to_dict(),
        "module": module_label,
        "file_path": str(path),
        "relative_path": record.relative_path,
        "source_parser": "java_parser",
        "imports": java_imports(repo_root, record, module_label),
    }
    # Normalize path/file fields then normalise parser metadata into the
    # canonical SourceMetadata dict so normalized bundles contain
    # consistent source metadata structures.
    from shared.provenance import normalize_paths

    canonical_meta = normalize_paths(parser_meta, root=repo_root)
    src = SourceMetadata.from_parser_metadata(canonical_meta).to_dict()
    # Parser-specific attributes live under `metadata` per the canonical
    # SourceMetadata contract; do not merge them into the top-level dict.
    repo_param = record.repository if module_label == record.repository else f"{record.repository}:{module_label}"
    from shared.provenance import ensure_provenance

    prov = ensure_provenance({"path": str(path), "stage": "java_parser", "module": module_label}, file_path=path, stage="java_parser", parser="java_parser", module=module_label)

    return NormalizedDocument(
        document_id=make_document_id("java_parser", repo_param, repo_root, path),
        text=text,
        source_parser="java_parser",
        source_metadata=src,
        provenance=prov,
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
