"""Build package-level relationship dicts for Java parser output."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def _package_name(entity: dict[str, Any]) -> str:
    return entity.get("qualified_name") or entity.get("name") or ""


def _package_parent(name: str) -> str:
    parts = name.split(".")
    return ".".join(parts[:-1]) if len(parts) > 1 else ""


def _import_target_package(import_entity: dict[str, Any]) -> str:
    name = import_entity.get("name", "")
    if not name:
        return ""
    if import_entity.get("is_wildcard"):
        name = name[:-2] if name.endswith(".*") else name
        if import_entity.get("is_static"):
            parts = name.split(".")
            return ".".join(parts[:-1]) if len(parts) > 1 else ""
        return name
    if import_entity.get("is_static"):
        parts = name.split(".")
        return ".".join(parts[:-2]) if len(parts) > 2 else ""
    parts = name.split(".")
    return ".".join(parts[:-1]) if len(parts) > 1 else ""


def _append_relationship(
    relationships: list[dict[str, Any]],
    seen: set[tuple[str, str, str]],
    rel_type: str,
    source: str,
    target: str,
    properties: dict[str, Any],
) -> None:
    key = (rel_type, source, target)
    if not source or not target or key in seen:
        return
    seen.add(key)
    relationships.append({"type": rel_type, "source": source, "target": target, "properties": properties})


def build_package_relationships(
    entities: Iterable[dict[str, Any]],
    module_label: str,
) -> list[dict[str, Any]]:
    """Create CONTAINS, IMPORTS, and BELONGS_TO relationships for packages."""
    entity_list = list(entities)
    packages = {
        _package_name(entity): entity
        for entity in entity_list
        if entity.get("type") == "Package" and _package_name(entity)
    }
    relationships: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for package_name in sorted(packages):
        package = packages[package_name]
        _append_relationship(
            relationships,
            seen,
            "BELONGS_TO",
            f"Package:{package_name}",
            f"Module:{module_label}",
            {
                "source_entity": package_name,
                "target_entity": module_label,
                "repository": package.get("repository", ""),
                "module": package.get("module", module_label),
                "file_path": package.get("file_path", ""),
            },
        )

        parent_name = _package_parent(package_name)
        if parent_name in packages:
            parent = packages[parent_name]
            _append_relationship(
                relationships,
                seen,
                "CONTAINS",
                f"Package:{parent_name}",
                f"Package:{package_name}",
                {
                    "source_entity": parent_name,
                    "target_entity": package_name,
                    "repository": parent.get("repository", ""),
                    "module": parent.get("module", module_label),
                    "file_path": parent.get("file_path", ""),
                },
            )

    for entity in entity_list:
        entity_type = entity.get("type")
        if entity_type in {"Class", "Interface", "Enum"}:
            source_package = entity.get("package", "")
            if source_package in packages:
                _append_relationship(
                    relationships,
                    seen,
                    "CONTAINS",
                    f"Package:{source_package}",
                    f"{entity_type}:{entity.get('qualified_name', entity.get('name', ''))}",
                    {
                        "source_entity": source_package,
                        "target_entity": entity.get("name", ""),
                        "repository": entity.get("repository", ""),
                        "module": entity.get("module", module_label),
                        "file_path": entity.get("file_path", ""),
                    },
                )
        elif entity_type == "Import":
            source_package = entity.get("package", "")
            target_package = _import_target_package(entity)
            if source_package in packages and target_package in packages:
                _append_relationship(
                    relationships,
                    seen,
                    "IMPORTS",
                    f"Package:{source_package}",
                    f"Package:{target_package}",
                    {
                        "source_entity": source_package,
                        "target_entity": target_package,
                        "repository": entity.get("repository", ""),
                        "module": entity.get("module", module_label),
                        "file_path": entity.get("file_path", ""),
                    },
                )

    return relationships