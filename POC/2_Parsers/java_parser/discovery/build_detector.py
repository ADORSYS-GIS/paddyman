"""Build-system detection for Java repositories.

Inspects directory contents to identify whether a project uses Maven, Gradle,
or neither, without executing any build commands.
"""
from __future__ import annotations

import logging
from pathlib import Path

from .models import BuildSystem

logger = logging.getLogger(__name__)

_MAVEN_FILES: frozenset[str] = frozenset({"pom.xml"})
_GRADLE_FILES: frozenset[str] = frozenset(
    {"build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"}
)


def detect_build_system(directory: Path) -> BuildSystem:
    """Return the primary build system detected in *directory*.

    When both Maven and Gradle indicators are present, Maven takes precedence
    (multi-module Maven projects occasionally vendor Gradle wrapper files).

    Args:
        directory: Path to inspect — must be an existing directory.

    Returns:
        :class:`BuildSystem` enum value.
    """
    if not directory.is_dir():
        logger.debug("Not a directory: %s", directory)
        return BuildSystem.UNKNOWN

    try:
        names = {entry.name for entry in directory.iterdir() if entry.is_file()}
    except OSError as exc:
        logger.warning("Cannot list directory %s: %s", directory, exc)
        return BuildSystem.UNKNOWN

    has_maven = bool(names & _MAVEN_FILES)
    has_gradle = bool(names & _GRADLE_FILES)

    if has_maven and has_gradle:
        logger.debug(
            "Both Maven and Gradle detected in %s — preferring Maven", directory
        )
        return BuildSystem.MAVEN

    if has_maven:
        return BuildSystem.MAVEN

    if has_gradle:
        return BuildSystem.GRADLE

    return BuildSystem.UNKNOWN


def find_pom_files(root: Path) -> list[Path]:
    """Return all ``pom.xml`` paths under *root*, sorted for determinism.

    Args:
        root: Repository or module root to search recursively.
    """
    try:
        return sorted(root.rglob("pom.xml"))
    except OSError as exc:
        logger.warning("Error scanning for pom.xml under %s: %s", root, exc)
        return []


def find_gradle_build_files(root: Path) -> list[Path]:
    """Return all Gradle build file paths under *root*, sorted for determinism.

    Includes ``build.gradle`` and ``build.gradle.kts`` variants.

    Args:
        root: Repository or module root to search recursively.
    """
    patterns = ("build.gradle", "build.gradle.kts")
    results: list[Path] = []
    for pattern in patterns:
        try:
            results.extend(root.rglob(pattern))
        except OSError as exc:
            logger.warning(
                "Error scanning for %s under %s: %s", pattern, root, exc
            )
    return sorted(results)


def find_build_files(root: Path) -> dict[BuildSystem, list[Path]]:
    """Return a mapping of build system to its build file paths under *root*.

    Args:
        root: Repository root to scan.

    Returns:
        Dict with :class:`BuildSystem` keys and lists of matching paths.
    """
    return {
        BuildSystem.MAVEN: find_pom_files(root),
        BuildSystem.GRADLE: find_gradle_build_files(root),
    }
