"""Parser for XML resource files.

Detects the semantic XML type (POM, Liquibase changelog, Spring context, or
generic) and delegates to the appropriate extractor.  Uses the standard library
:mod:`xml.etree.ElementTree` throughout.
"""
from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .models import XmlType
from .pom_parser import parse_pom_file

logger = logging.getLogger(__name__)

_LIQUIBASE_TAG_HINTS = frozenset({"databasechangelog", "databaseChangeLog"})


def _local(elem: ET.Element) -> str:
    """Return the local (namespace-stripped) tag name of *elem*."""
    tag = elem.tag
    return tag.split("}")[-1] if "}" in tag else tag


def _elem_ns(elem: ET.Element) -> str:
    """Return the namespace URI of *elem*, or an empty string."""
    tag = elem.tag
    return tag[1 : tag.index("}")] if tag.startswith("{") else ""


def _detect_xml_type(path: Path, root: ET.Element) -> XmlType:
    """Classify an XML file by its root element and/or filename.

    Checks (in order):
    1. Filename equals ``pom.xml`` → :attr:`XmlType.POM`.
    2. Root local name or namespace hints at Liquibase → :attr:`XmlType.LIQUIBASE`.
    3. Root namespace or local name hints at Spring beans → :attr:`XmlType.SPRING`.
    4. Fallthrough → :attr:`XmlType.GENERIC`.
    """
    if path.name == "pom.xml":
        return XmlType.POM

    local = _local(root).lower()
    ns = _elem_ns(root).lower()

    if "liquibase" in ns or local in ("databasechangelog",):
        return XmlType.LIQUIBASE

    if "springframework.org/schema/beans" in ns or local in ("beans", "application-context"):
        return XmlType.SPRING

    return XmlType.GENERIC


def _parse_liquibase_xml(root: ET.Element) -> dict[str, Any]:
    """Extract changeset summaries from a Liquibase database changelog.

    Returns a dict with ``changeset_count`` and a ``changesets`` list where
    each entry contains ``id``, ``author``, and ``context``.
    """
    changesets: list[dict[str, str]] = []
    for child in root:
        if _local(child).lower() == "changeset":
            changesets.append(
                {
                    "id": child.get("id", ""),
                    "author": child.get("author", ""),
                    "context": child.get("context", ""),
                }
            )
    return {"changeset_count": len(changesets), "changesets": changesets}


def _parse_spring_xml(root: ET.Element) -> dict[str, Any]:
    """Extract bean definitions from a Spring XML application context.

    Returns a dict with ``bean_count`` and a ``beans`` list where each entry
    contains ``id`` and ``class``.
    """
    beans: list[dict[str, str]] = []
    for child in root:
        if _local(child).lower() == "bean":
            beans.append(
                {
                    "id": child.get("id", child.get("name", "")),
                    "class": child.get("class", ""),
                }
            )
    return {"bean_count": len(beans), "beans": beans}


def _parse_generic_xml(root: ET.Element) -> dict[str, Any]:
    """Summarise an unknown XML file by its root element and direct children."""
    child_tags = sorted(
        {_local(child) for child in root}
    )
    return {"root_element": _local(root), "child_elements": child_tags}


def parse_xml_file(path: Path) -> tuple[XmlType, dict[str, Any], list[str]]:
    """Parse an XML resource file and dispatch to the appropriate extractor.

    Args:
        path: Absolute path to the XML file.

    Returns:
        ``(xml_type, content_dict, error_list)`` — error list is empty on
        success.
    """
    errors: list[str] = []
    try:
        tree = ET.parse(path)  # noqa: S314 — trusted local file
    except ET.ParseError as exc:
        errors.append(f"XML parse error in {path}: {exc}")
        return XmlType.GENERIC, {}, errors
    except OSError as exc:
        errors.append(f"Cannot read {path}: {exc}")
        return XmlType.GENERIC, {}, errors

    root = tree.getroot()
    xml_type = _detect_xml_type(path, root)

    if xml_type == XmlType.POM:
        content, pom_errors = parse_pom_file(path)
        return xml_type, content, pom_errors
    if xml_type == XmlType.LIQUIBASE:
        return xml_type, _parse_liquibase_xml(root), errors
    if xml_type == XmlType.SPRING:
        return xml_type, _parse_spring_xml(root), errors
    return xml_type, _parse_generic_xml(root), errors
