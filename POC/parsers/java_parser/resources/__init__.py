"""Spring Boot resource file scanner and parser.

Public API for Chunk 1.7 of the Java Parser pipeline.

Typical usage::

    from java_parser.resources import scan_and_parse_resources, ResourceSummary

    summary: ResourceSummary = scan_and_parse_resources(repo_root)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import ParsedResource, ResourceFile, ResourceFileType, XmlType
from .properties_parser import parse_properties_file
from .scanner import find_resource_files
from .xml_parser import parse_xml_file
from .yaml_parser import parse_yaml_file

logger = logging.getLogger(__name__)

__all__ = [
    "ParsedResource",
    "ResourceFile",
    "ResourceFileType",
    "ResourceSummary",
    "XmlType",
    "scan_and_parse_resources",
]


@dataclass
class ResourceSummary:
    """Aggregated counts from resource file discovery and parsing."""

    total_files: int = 0
    properties_count: int = 0
    yaml_count: int = 0
    xml_count: int = 0
    pom_count: int = 0
    migration_count: int = 0
    config_keys: int = 0
    maven_deps: int = 0
    errors: int = 0


def _parse_resource(
    record: ResourceFile, repo_root: Path
) -> tuple[ParsedResource, ResourceSummary]:
    """Parse one resource file and return the result with incremental counts."""
    s = ResourceSummary(total_files=1)
    abs_path = repo_root / record.relative_path
    content: dict[str, Any] = {}
    xml_type_value: str | None = None
    errors: list[str] = []

    try:
        if record.file_type == ResourceFileType.PROPERTIES.value:
            s.properties_count = 1
            kv, errors = parse_properties_file(abs_path)
            content = {"keys": kv}
            s.config_keys = len(kv)

        elif record.file_type == ResourceFileType.YAML.value:
            s.yaml_count = 1
            parsed, errors = parse_yaml_file(abs_path)
            content = parsed
            flat = parsed.get("flat", {})
            s.config_keys = len(flat) if isinstance(flat, dict) else 0

        else:  # XML
            s.xml_count = 1
            xt, parsed, errors = parse_xml_file(abs_path)
            xml_type_value = xt.value
            content = parsed
            if xt == XmlType.POM:
                s.pom_count = 1
                s.maven_deps = len(parsed.get("dependencies", []))
            elif xt == XmlType.LIQUIBASE:
                s.migration_count = 1

    except Exception as exc:  # noqa: BLE001
        errors.append(f"Unexpected error parsing {record.relative_path}: {exc}")

    if errors:
        s.errors = 1
        for msg in errors:
            logger.warning(msg)

    return (
        ParsedResource(
            repository=record.repository,
            module=record.module,
            file=record.file,
            relative_path=record.relative_path,
            file_type=record.file_type,
            xml_type=xml_type_value,
            content=content,
            parse_errors=errors,
        ),
        s,
    )


def _accumulate(total: ResourceSummary, part: ResourceSummary) -> None:
    total.total_files += part.total_files
    total.properties_count += part.properties_count
    total.yaml_count += part.yaml_count
    total.xml_count += part.xml_count
    total.pom_count += part.pom_count
    total.migration_count += part.migration_count
    total.config_keys += part.config_keys
    total.maven_deps += part.maven_deps
    total.errors += part.errors


def scan_and_parse_resources(
    repo_root: Path,
    module_paths: list[Path] | None = None,
) -> ResourceSummary:
    """Discover and parse all resource files under *repo_root*.

    Scans for ``.properties``, ``.yml``, ``.yaml``, and ``.xml`` files,
    skipping build-output directories.  Parsing failures are non-fatal.

    Args:
        repo_root:    Absolute path to the repository root.
        module_paths: Absolute module root directories used for module-label
                      assignment.  Defaults to ``[repo_root]``.

    Returns:
        :class:`ResourceSummary` with aggregated counts.
    """
    effective_module_paths = module_paths if module_paths is not None else [repo_root]
    records = find_resource_files(
        repo_root, effective_module_paths, repository=repo_root.name
    )
    summary = ResourceSummary()
    for record in records:
        _, part = _parse_resource(record, repo_root)
        _accumulate(summary, part)
    logger.info(
        "Resources %s: %d files (%d props, %d yaml, %d xml [%d pom, %d migration], %d errors)",
        repo_root.name,
        summary.total_files,
        summary.properties_count,
        summary.yaml_count,
        summary.xml_count,
        summary.pom_count,
        summary.migration_count,
        summary.errors,
    )
    return summary
