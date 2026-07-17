"""Parser for Maven ``pom.xml`` files.

Extracts project coordinates, parent info, modules, properties, dependencies,
and build plugins using the standard library :mod:`xml.etree.ElementTree`.
Handles both namespaced (``http://maven.apache.org/POM/4.0.0``) and plain XML.
"""
from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _detect_ns(elem: ET.Element) -> str:
    """Return the XML namespace URI of *elem*, or an empty string."""
    tag = elem.tag
    return tag[1 : tag.index("}")] if tag.startswith("{") else ""


def _text(elem: ET.Element, tag: str, ns: str) -> str:
    """Return stripped text of the first child whose local name is *tag*."""
    full_tag = f"{{{ns}}}{tag}" if ns else tag
    child = elem.find(full_tag)
    return child.text.strip() if child is not None and child.text else ""


def _extract_parent(root: ET.Element, ns: str) -> dict[str, str] | None:
    """Extract ``<parent>`` coordinates, or ``None`` if absent."""
    parent_elem = root.find(f"{{{ns}}}parent" if ns else "parent")
    if parent_elem is None:
        return None
    return {
        "groupId": _text(parent_elem, "groupId", ns),
        "artifactId": _text(parent_elem, "artifactId", ns),
        "version": _text(parent_elem, "version", ns),
    }


def _extract_properties(root: ET.Element, ns: str) -> dict[str, str]:
    """Extract all ``<properties>`` child elements as a flat dict."""
    props_elem = root.find(f"{{{ns}}}properties" if ns else "properties")
    if props_elem is None:
        return {}
    result: dict[str, str] = {}
    for child in props_elem:
        local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        result[local] = (child.text or "").strip()
    return result


def _extract_modules(root: ET.Element, ns: str) -> list[str]:
    """Return sub-module names listed under ``<modules>``."""
    modules_elem = root.find(f"{{{ns}}}modules" if ns else "modules")
    if modules_elem is None:
        return []
    mod_tag = f"{{{ns}}}module" if ns else "module"
    return [m.text.strip() for m in modules_elem.findall(mod_tag) if m.text]


def _extract_deps(container: ET.Element, ns: str) -> list[dict[str, str]]:
    """Extract dependency entries from a ``<dependencies>`` container."""
    deps_elem = container.find(f"{{{ns}}}dependencies" if ns else "dependencies")
    if deps_elem is None:
        return []
    dep_tag = f"{{{ns}}}dependency" if ns else "dependency"
    result: list[dict[str, str]] = []
    for dep in deps_elem.findall(dep_tag):
        entry: dict[str, str] = {
            "groupId": _text(dep, "groupId", ns),
            "artifactId": _text(dep, "artifactId", ns),
        }
        for optional in ("version", "scope"):
            val = _text(dep, optional, ns)
            if val:
                entry[optional] = val
        result.append(entry)
    return result


def _extract_plugins(root: ET.Element, ns: str) -> list[dict[str, str]]:
    """Extract plugin entries from ``<build><plugins>``."""
    build_elem = root.find(f"{{{ns}}}build" if ns else "build")
    if build_elem is None:
        return []
    plugins_elem = build_elem.find(f"{{{ns}}}plugins" if ns else "plugins")
    if plugins_elem is None:
        return []
    plugin_tag = f"{{{ns}}}plugin" if ns else "plugin"
    result: list[dict[str, str]] = []
    for plugin in plugins_elem.findall(plugin_tag):
        entry: dict[str, str] = {
            "groupId": _text(plugin, "groupId", ns),
            "artifactId": _text(plugin, "artifactId", ns),
        }
        ver = _text(plugin, "version", ns)
        if ver:
            entry["version"] = ver
        result.append(entry)
    return result


def parse_pom_file(path: Path) -> tuple[dict[str, Any], list[str]]:
    """Extract Maven POM metadata from *path*.

    Args:
        path: Absolute path to a ``pom.xml`` file.

    Returns:
        ``(content_dict, error_list)`` — error list is empty on success.
    """
    errors: list[str] = []
    try:
        tree = ET.parse(path)  # noqa: S314 — trusted local file
    except ET.ParseError as exc:
        errors.append(f"XML parse error in {path}: {exc}")
        return {}, errors
    except OSError as exc:
        errors.append(f"Cannot read {path}: {exc}")
        return {}, errors

    root = tree.getroot()
    ns = _detect_ns(root)

    content: dict[str, Any] = {
        "groupId": _text(root, "groupId", ns),
        "artifactId": _text(root, "artifactId", ns),
        "version": _text(root, "version", ns),
        "packaging": _text(root, "packaging", ns) or "jar",
        "parent": _extract_parent(root, ns),
        "modules": _extract_modules(root, ns),
        "properties": _extract_properties(root, ns),
        "dependencies": _extract_deps(root, ns),
        "plugins": _extract_plugins(root, ns),
    }
    return content, errors
