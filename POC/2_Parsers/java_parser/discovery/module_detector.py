"""Maven and Gradle module detection.

Resolves the sub-module directories declared in ``pom.xml`` (Maven) and
``settings.gradle`` / ``settings.gradle.kts`` (Gradle) without executing
any build commands.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from .build_detector import detect_build_system
from .dependency_detector import extract_maven_metadata
from .models import BuildSystem

logger = logging.getLogger(__name__)

# Matches: include(':sub-project')  or  include 'sub-project'
_RE_GRADLE_INCLUDE = re.compile(
    r"""include\s*\(?\s*['"]([^'"]+)['"]\s*\)?""",
    re.MULTILINE,
)

_SETTINGS_CANDIDATES = ("settings.gradle", "settings.gradle.kts")


def _gradle_module_paths(repo_root: Path) -> list[Path]:
    """Resolve Gradle sub-project paths from the settings file.

    Gradle project paths use colon notation (e.g. ``:api`` → ``api/``).
    Nested projects (``':core:util'``) resolve to ``core/util/``.

    Args:
        repo_root: Repository root containing the settings file.

    Returns:
        List of existing sub-module directories.
    """
    settings_file: Path | None = None
    for name in _SETTINGS_CANDIDATES:
        candidate = repo_root / name
        if candidate.is_file():
            settings_file = candidate
            break

    if settings_file is None:
        return []

    try:
        content = settings_file.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.warning("Cannot read %s: %s", settings_file, exc)
        return []

    paths: list[Path] = []
    for match in _RE_GRADLE_INCLUDE.finditer(content):
        raw = match.group(1).lstrip(":")  # ':api' → 'api'
        sub_dir = repo_root / raw.replace(":", "/")
        if sub_dir.is_dir():
            paths.append(sub_dir)
        else:
            logger.debug("Declared Gradle sub-project not found: %s", sub_dir)

    return paths


def _maven_module_paths(repo_root: Path) -> list[Path]:
    """Resolve Maven sub-module directories from the root ``pom.xml``.

    Args:
        repo_root: Repository root containing the root ``pom.xml``.

    Returns:
        List of existing sub-module directories.
    """
    root_pom = repo_root / "pom.xml"
    if not root_pom.is_file():
        return []

    metadata = extract_maven_metadata(root_pom)
    if metadata is None or not metadata.declared_modules:
        return []

    paths: list[Path] = []
    for module_name in metadata.declared_modules:
        sub_dir = repo_root / module_name
        if sub_dir.is_dir():
            paths.append(sub_dir)
        else:
            logger.debug(
                "Declared Maven module directory not found: %s", sub_dir
            )
    return paths


def detect_modules(repo_root: Path) -> list[Path]:
    """Return the list of detected module root directories for *repo_root*.

    Detects the build system at *repo_root* and delegates to the appropriate
    resolver.  When no modules are declared, returns ``[repo_root]`` so that
    callers can treat a single-module repo uniformly.

    Args:
        repo_root: Absolute path to the repository root.

    Returns:
        Non-empty list of module root directories, guaranteed to exist.
    """
    build_system = detect_build_system(repo_root)

    if build_system == BuildSystem.MAVEN:
        module_paths = _maven_module_paths(repo_root)
    elif build_system == BuildSystem.GRADLE:
        module_paths = _gradle_module_paths(repo_root)
    else:
        module_paths = []

    if not module_paths:
        logger.debug(
            "No sub-modules found in %s — treating as single-module project",
            repo_root,
        )
        return [repo_root]

    return module_paths


def module_name(module_path: Path, repo_root: Path) -> str:
    """Derive a human-readable module name from *module_path*.

    Returns the path relative to *repo_root*, using forward slashes.

    Args:
        module_path: Absolute path to the module directory.
        repo_root:   Absolute path to the repository root.

    Returns:
        Relative path string, e.g. ``"consent-management/consent-core-api"``.
    """
    try:
        return module_path.relative_to(repo_root).as_posix()
    except ValueError:
        return module_path.name
