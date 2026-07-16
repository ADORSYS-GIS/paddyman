"""Gradle metadata extraction.

Parses ``settings.gradle`` / ``settings.gradle.kts`` and ``build.gradle`` /
``build.gradle.kts`` using lightweight regex — no Gradle execution required.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from .models import GradleMetadata

logger = logging.getLogger(__name__)

# Matches: rootProject.name = 'foo'  or  rootProject.name = "foo"
_RE_ROOT_NAME = re.compile(r"""rootProject\.name\s*=\s*['"]([^'"]+)['"]""")

# Matches: includeBuild('path')  or  includeBuild("path")
_RE_INCLUDE_BUILD = re.compile(r"""includeBuild\s*\(\s*['"]([^'"]+)['"]\s*\)""")

# Matches: project(':module-name')  or  project(":module-name")
_RE_PROJECT_DEP = re.compile(r"""project\s*\(\s*['"]([^'"]+)['"]\s*\)""")

_SETTINGS_FILES = ("settings.gradle", "settings.gradle.kts")
_BUILD_FILES = ("build.gradle", "build.gradle.kts")


def _read(path: Path) -> str:
    """Return text content of *path*, or an empty string on error."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.warning("Cannot read %s: %s", path, exc)
        return ""


def _find_file(directory: Path, candidates: tuple[str, ...]) -> Path | None:
    """Return the first existing candidate file inside *directory*."""
    for name in candidates:
        path = directory / name
        if path.is_file():
            return path
    return None


def extract_gradle_metadata(module_path: Path) -> GradleMetadata | None:
    """Extract Gradle metadata from *module_path*.

    Reads the settings file for ``rootProject.name`` and ``includeBuild``
    declarations, then reads the build file for ``project()`` dependencies.

    Returns ``None`` when no Gradle files are found in *module_path*.

    Args:
        module_path: Directory containing Gradle build files.
    """
    settings_file = _find_file(module_path, _SETTINGS_FILES)
    build_file = _find_file(module_path, _BUILD_FILES)

    if settings_file is None and build_file is None:
        return None

    project_name: str | None = None
    included_builds: list[str] = []
    project_dependencies: list[str] = []

    if settings_file is not None:
        content = _read(settings_file)
        match = _RE_ROOT_NAME.search(content)
        if match:
            project_name = match.group(1)
        included_builds = _RE_INCLUDE_BUILD.findall(content)

    if build_file is not None:
        content = _read(build_file)
        project_dependencies = _RE_PROJECT_DEP.findall(content)

    return GradleMetadata(
        project_name=project_name,
        included_builds=included_builds,
        project_dependencies=project_dependencies,
    )
