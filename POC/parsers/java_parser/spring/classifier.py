"""Spring component classifier.

Walks a tree-sitter Java AST root node, extracts Spring annotations from each
class declaration, classifies the component type, and assembles
:class:`~java_parser.spring.models.SpringComponentResult` objects.

Intended to be composed on top of the existing AST extraction phase:
parse with :func:`~java_parser.java_ast.extractor.extract_file_ast`, then
call :func:`extract_spring_components` with the same root node and the
returned :class:`~java_parser.java_ast.models.JavaFileAst`.
"""
from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Node

from java_parser.java_ast.extractor import extract_file_ast
from java_parser.java_ast.models import JavaFileAst
from java_parser.java_ast.node_helpers import child_of_type, node_text
from java_parser.java_ast.parser import parse_bytes
from java_parser.spring.annotation_extractor import extract_spring_annotations
from java_parser.spring.models import (
    HTTP_METHOD_MAP,
    SpringAnnotation,
    SpringComponentResult,
    resolve_component_type,
)

logger = logging.getLogger(__name__)

_CLASS_DECLARATION_TYPES: frozenset[str] = frozenset(
    {"class_declaration", "interface_declaration", "enum_declaration"}
)


# ── Path extraction from annotation values ─────────────────────────────────────


def _collect_paths(annotations: list[SpringAnnotation]) -> list[str]:
    """Return URL paths extracted from mapping annotation values and attributes."""
    paths: list[str] = []
    for ann in annotations:
        if ann.value:
            paths.append(ann.value)
        if "value" in ann.attributes:
            paths.append(ann.attributes["value"])
        if "_extra_paths" in ann.attributes:
            paths.extend(ann.attributes["_extra_paths"].split(","))
    return [p for p in paths if p]


def _collect_http_methods(annotation_names: list[str]) -> list[str]:
    """Return HTTP verbs inferred from mapping annotation names."""
    seen: list[str] = []
    for name in annotation_names:
        method = HTTP_METHOD_MAP.get(name)
        if method and method not in seen:
            seen.append(method)
    return seen


# ── AST traversal ──────────────────────────────────────────────────────────────


def _class_name(decl_node: Node) -> str:
    """Return the simple class/interface/enum name from a declaration node."""
    ident = child_of_type(decl_node, "identifier")
    return node_text(ident) if ident else ""


def _process_declaration(
    node: Node,
    package: str,
    file_path: str,
    repository: str,
    module: str,
) -> SpringComponentResult | None:
    """Build a :class:`SpringComponentResult` from a single declaration node.

    Returns ``None`` when the declaration carries no Spring annotations.
    """
    mods_node = child_of_type(node, "modifiers")
    if mods_node is None:
        return None

    spring_annotations = extract_spring_annotations(mods_node)
    if not spring_annotations:
        return None

    annotation_names = [a.name for a in spring_annotations]
    component_type = resolve_component_type(annotation_names)
    if component_type is None:
        return None

    class_name = _class_name(node)
    mapped_paths = _collect_paths(spring_annotations)
    http_methods = _collect_http_methods(annotation_names)

    return SpringComponentResult(
        component_type=component_type,
        class_name=class_name,
        annotations=annotation_names,
        annotation_details=spring_annotations,
        package=package,
        file_path=file_path,
        repository=repository,
        module=module,
        mapped_paths=mapped_paths,
        http_methods=http_methods,
    )


# ── Public API ─────────────────────────────────────────────────────────────────


def extract_spring_components(
    root: Node,
    file_ast: JavaFileAst,
) -> list[SpringComponentResult]:
    """Extract Spring component metadata from a tree-sitter AST root.

    Args:
        root:     Root node of the parsed Java source file.
        file_ast: Corresponding :class:`JavaFileAst` produced by
                  :func:`~java_parser.java_ast.extractor.extract_file_ast`.
                  Provides package, file path, repository, and module context.

    Returns:
        List of :class:`SpringComponentResult` instances — one per class
        declaration that carries at least one recognised Spring annotation.
        An empty list is returned for files with no Spring annotations.
    """
    results: list[SpringComponentResult] = []
    for child in root.children:
        if child.type not in _CLASS_DECLARATION_TYPES:
            continue
        try:
            result = _process_declaration(
                child,
                package=file_ast.package,
                file_path=file_ast.file_path,
                repository=file_ast.repository,
                module=file_ast.module,
            )
            if result is not None:
                results.append(result)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Skipping Spring extraction for declaration in %s: %s",
                file_ast.file_path,
                exc,
            )
    return results


def extract_spring_from_source(
    source: bytes,
    *,
    file_path: str = "",
    repository: str = "",
    module: str = "",
) -> list[SpringComponentResult]:
    """Parse *source* bytes and extract Spring component metadata.

    Convenience wrapper that combines :func:`parse_bytes`,
    :func:`~java_parser.java_ast.extractor.extract_file_ast`, and
    :func:`extract_spring_components` into a single call.

    Args:
        source:     Raw Java source bytes.
        file_path:  Repository-relative path (for provenance only).
        repository: Repository name (for provenance only).
        module:     Module label (for provenance only).

    Returns:
        List of :class:`SpringComponentResult` instances.
    """
    root = parse_bytes(source)
    file_ast = extract_file_ast(
        root, file_path=file_path, repository=repository, module=module
    )
    return extract_spring_components(root, file_ast)
