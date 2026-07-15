"""Java AST extractor.

Walks a tree-sitter parse tree and extracts package declarations, imports,
and top-level type declarations (classes, interfaces, enums).

Deliberately excludes: method bodies, field declarations, Spring annotations,
and nested type declarations — those belong to later pipeline stages.
"""
from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Node

from .models import JavaFileAst
from .import_extractor import extract_imports, extract_import_declarations
from .declaration_extractors import DECLARATION_EXTRACTORS
from .node_helpers import child_of_type, node_text

logger = logging.getLogger(__name__)


def _extract_package(root: Node) -> str:
    """Extract package declaration from AST root node."""
    for child in root.children:
        if child.type == "package_declaration":
            for part in child.children:
                if part.type in ("scoped_identifier", "identifier"):
                    return node_text(part)
    return ""


def _extract_declarations(
    root: Node, package: str, file_path: str, repository: str, module: str
) -> list:
    """Extract all type declarations from AST root node."""
    declarations = []
    for child in root.children:
        extractor = DECLARATION_EXTRACTORS.get(child.type)
        if extractor is None:
            continue
        try:
            decl = extractor(child, package, file_path, repository, module)
            declarations.append(decl)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipping declaration in %s: %s", file_path, exc)
    return declarations


def extract_file_ast(
    root: Node,
    *,
    file_path: str,
    repository: str,
    module: str,
) -> JavaFileAst:
    """Extract structured metadata from a tree-sitter parse tree.

    Args:
        root:       Root node of the parsed Java source file.
        file_path:  Repository-relative path to the source file.
        repository: Repository name (for provenance tracking).
        module:     Module label (for provenance tracking).

    Returns:
        :class:`JavaFileAst` with package, imports, and type declarations.
    """
    has_errors = root.has_error
    error_msg = "Syntax errors detected by tree-sitter parser" if has_errors else None

    package = _extract_package(root)
    imports = extract_imports(root)
    import_declarations = extract_import_declarations(
        root, package, file_path, repository, module
    )
    declarations = _extract_declarations(root, package, file_path, repository, module)

    return JavaFileAst(
        file_path=file_path,
        repository=repository,
        module=module,
        package=package,
        imports=imports,
        import_declarations=import_declarations,
        declarations=declarations,
        has_errors=has_errors,
        error_message=error_msg,
    )


def parse_and_extract(
    path: Path,
    *,
    repository: str = "",
    module: str = "",
    repo_root: Path | None = None,
) -> JavaFileAst:
    """Read *path*, parse it, and return extracted AST metadata.

    Args:
        path:       Absolute path to the ``.java`` file.
        repository: Repository name for provenance.
        module:     Module label for provenance.
        repo_root:  When supplied, ``file_path`` in the result is relative to
                    this directory.  Otherwise the bare filename is used.
    """
    from .parser import parse_file  # local import avoids circular dependency

    try:
        root, _ = parse_file(path)
    except OSError as exc:
        logger.error("Cannot read %s: %s", path, exc)
        rel = path.relative_to(repo_root).as_posix() if repo_root else path.name
        return JavaFileAst(
            file_path=rel,
            repository=repository,
            module=module,
            package="",
            has_errors=True,
            error_message=str(exc),
        )

    if repo_root:
        try:
            file_path = path.relative_to(repo_root).as_posix()
        except ValueError:
            file_path = path.name
    else:
        file_path = path.name

    return extract_file_ast(root, file_path=file_path, repository=repository, module=module)
