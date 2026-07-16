"""Java source file scanning and metadata extraction.

Discovers ``.java`` files within a directory tree and extracts:
- package declaration
- source root (conventional ``src/main/java`` / ``src/test/java`` locations)
- line count
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Standard Maven / Gradle source roots in priority order
_SOURCE_ROOTS = (
    "src/main/java",
    "src/test/java",
    "src/main/groovy",
    "src/test/groovy",
    "src",
)

# Matches the Java package declaration: package com.example.foo;
_RE_PACKAGE = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.MULTILINE)

# Max bytes to scan for the package declaration (avoids loading huge files)
_PACKAGE_SCAN_BYTES = 4096


def find_java_files(root: Path) -> list[Path]:
    """Return all ``.java`` files under *root*, sorted for determinism.

    Args:
        root: Directory to scan recursively.
    """
    try:
        return sorted(root.rglob("*.java"))
    except OSError as exc:
        logger.warning("Error scanning for .java files under %s: %s", root, exc)
        return []


def extract_package(java_file: Path) -> str:
    """Return the package declared in *java_file*, or an empty string.

    Reads only the first :data:`_PACKAGE_SCAN_BYTES` bytes to keep scanning
    efficient on large files.

    Args:
        java_file: Absolute path to the ``.java`` source file.
    """
    try:
        with java_file.open("rb") as fh:
            raw = fh.read(_PACKAGE_SCAN_BYTES)
        text = raw.decode("utf-8", errors="replace")
    except OSError as exc:
        logger.debug("Cannot read %s for package extraction: %s", java_file, exc)
        return ""

    match = _RE_PACKAGE.search(text)
    return match.group(1) if match else ""


def count_lines(java_file: Path) -> int:
    """Return the total line count of *java_file*.

    Returns 0 on read error.

    Args:
        java_file: Absolute path to the ``.java`` source file.
    """
    try:
        with java_file.open("rb") as fh:
            return sum(1 for _ in fh)
    except OSError as exc:
        logger.debug("Cannot count lines in %s: %s", java_file, exc)
        return 0


def detect_source_root(java_file: Path, module_root: Path) -> str:
    """Infer the source root directory for *java_file* relative to *module_root*.

    Checks conventional source-root directories first.  Falls back to deriving
    the root from the declared package by stripping the package path suffix.

    Args:
        java_file:   Absolute path to the ``.java`` file.
        module_root: Root of the module that owns this file.

    Returns:
        Source root as a POSIX string relative to *module_root*, or an empty
        string when it cannot be determined.
    """
    # Fast path: check standard source roots
    for candidate in _SOURCE_ROOTS:
        src_root = module_root / candidate
        if src_root.is_dir():
            try:
                java_file.relative_to(src_root)
                return candidate
            except ValueError:
                pass

    # Fallback: derive root from package declaration
    package = extract_package(java_file)
    if not package:
        return ""

    package_parts = package.split(".")
    parent = java_file.parent
    for _ in package_parts:
        parent = parent.parent

    try:
        return parent.relative_to(module_root).as_posix()
    except ValueError:
        return ""
