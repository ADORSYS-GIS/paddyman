"""Tree-sitter Java parser initialisation and low-level parsing utilities.

This module creates a single :class:`tree_sitter.Parser` instance per process
(the grammar shared object is reloaded only once) and exposes thin wrappers
for parsing bytes and files.

**Technology choice — tree-sitter-java**

Tree-sitter was selected over JavaParser (JVM-based) and Eclipse JDT (JVM,
heavyweight) for the following reasons:

- Pure-Python integration via the ``tree-sitter`` and ``tree-sitter-java``
  PyPI packages — no JVM required.
- Error-resilient: tree-sitter always returns a parse tree even for
  syntactically invalid input; error nodes are flagged explicitly.
- Fast incremental parsing suitable for large repositories.
- Small footprint relative to JVM alternatives.
- Active maintenance with a stable Python API.
"""
from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Language, Node, Parser

logger = logging.getLogger(__name__)

# ── Singleton setup ────────────────────────────────────────────────────────────

_parser: Parser | None = None
_language: Language | None = None


def _get_parser() -> Parser:
    """Return the shared tree-sitter Java :class:`~tree_sitter.Parser`.

    The parser and its grammar are initialised lazily on the first call and
    reused for all subsequent calls.

    Raises:
        ImportError: when ``tree-sitter-java`` is not installed.
        RuntimeError: when the grammar fails to load.
    """
    global _parser, _language  # noqa: PLW0603

    if _parser is not None:
        return _parser

    try:
        import tree_sitter_java  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "tree-sitter-java is required for Java AST parsing. "
            "Add 'tree-sitter-java>=0.23.0' to POC/requirements.txt and "
            "reinstall the virtual environment."
        ) from exc

    try:
        _language = Language(tree_sitter_java.language())
        _parser = Parser(_language)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"Failed to initialise tree-sitter Java grammar: {exc}"
        ) from exc

    logger.debug("tree-sitter Java grammar initialised")
    return _parser


# ── Public parsing helpers ─────────────────────────────────────────────────────


def parse_bytes(source: bytes) -> Node:
    """Parse *source* and return the root AST node.

    tree-sitter always returns a valid tree; callers should check
    :attr:`~tree_sitter.Node.has_error` on the returned node to detect
    syntax problems.

    Args:
        source: UTF-8-encoded Java source bytes.

    Returns:
        Root ``program`` node of the parse tree.
    """
    return _get_parser().parse(source).root_node


def parse_file(path: Path) -> tuple[Node, bytes]:
    """Read *path* and parse it as a Java source file.

    Args:
        path: Absolute or relative path to a ``.java`` file.

    Returns:
        A ``(root_node, source_bytes)`` tuple.  *source_bytes* is kept so
        callers can decode node text without re-reading the file.

    Raises:
        OSError: when the file cannot be read.
    """
    source = path.read_bytes()
    root = parse_bytes(source)
    if root.has_error:
        logger.debug("Syntax errors detected in %s", path)
    return root, source
