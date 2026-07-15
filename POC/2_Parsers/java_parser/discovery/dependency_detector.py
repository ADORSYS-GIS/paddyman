"""Maven dependency and metadata extraction.

Parses ``pom.xml`` files using the standard library XML parser.  Handles the
Maven POM XML namespace transparently.
"""
from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from .models import MavenMetadata

logger = logging.getLogger(__name__)

_NS = "http://maven.apache.org/POM/4.0.0"
_NS_MAP = {"m": _NS}


def _text(element: ET.Element | None) -> str | None:
    """Return stripped text content of *element*, or None when missing."""
    if element is None:
        return None
    value = (element.text or "").strip()
    return value or None


def _tag(local: str) -> str:
    """Build a fully-qualified tag name using the Maven POM namespace."""
    return f"{{{_NS}}}{local}"


def extract_maven_metadata(pom_path: Path) -> MavenMetadata | None:
    """Parse *pom_path* and return a :class:`MavenMetadata` instance.

    Returns ``None`` when the file cannot be read or parsed.

    Args:
        pom_path: Absolute path to the ``pom.xml`` file.
    """
    try:
        tree = ET.parse(pom_path)  # noqa: S314 — local files only
    except (ET.ParseError, OSError) as exc:
        logger.warning("Cannot parse %s: %s", pom_path, exc)
        return None

    root = tree.getroot()

    # Strip namespace when present so we can query with or without it.
    def _find(tag: str) -> ET.Element | None:
        element = root.find(_tag(tag))
        if element is None:
            element = root.find(tag)
        return element

    def _find_in(parent: ET.Element | None, tag: str) -> ET.Element | None:
        if parent is None:
            return None
        element = parent.find(_tag(tag))
        if element is None:
            element = parent.find(tag)
        return element

    group_id = _text(_find("groupId"))
    artifact_id = _text(_find("artifactId"))

    if not artifact_id:
        logger.warning("Missing <artifactId> in %s — skipping", pom_path)
        return None

    parent_el = _find("parent")
    parent_group = _text(_find_in(parent_el, "groupId"))
    parent_artifact = _text(_find_in(parent_el, "artifactId"))
    parent_version = _text(_find_in(parent_el, "version"))

    # Inherit groupId from parent when not declared locally
    effective_group = group_id or parent_group or ""

    version = _text(_find("version")) or parent_version

    # Sub-modules declared in <modules>
    modules_el = _find("modules")
    declared_modules: list[str] = []
    if modules_el is not None:
        for mod in modules_el:
            name = _text(mod)
            if name:
                declared_modules.append(name)

    # Direct dependencies (not managed — those are in <dependencyManagement>)
    deps_el = _find("dependencies")
    dependencies: list[dict[str, str]] = []
    if deps_el is not None:
        for dep in deps_el:
            dep_group = _text(_find_in(dep, "groupId")) or ""
            dep_artifact = _text(_find_in(dep, "artifactId")) or ""
            dep_version = _text(_find_in(dep, "version")) or ""
            if dep_group or dep_artifact:
                dependencies.append(
                    {
                        "groupId": dep_group,
                        "artifactId": dep_artifact,
                        "version": dep_version,
                    }
                )

    return MavenMetadata(
        group_id=effective_group,
        artifact_id=artifact_id,
        version=version,
        parent_group_id=parent_group,
        parent_artifact_id=parent_artifact,
        parent_version=parent_version,
        declared_modules=declared_modules,
        dependencies=dependencies,
    )
