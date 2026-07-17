"""Build IMPORTS relationship dicts from Java import declarations.

Creates relationships between type declarations (Class, Interface, Enum)
and their import statements.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def build_imports_relationships(
    file_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create IMPORTS relationships from type entities to import entities.

    Each type declaration (Class, Interface, Enum) in a file uses the imports
    declared in that file.

    Args:
        file_entities: All entities extracted from one Java file.

    Returns:
        List of relationship dicts with type ``"IMPORTS"``.
    """
    # Separate imports from type declarations
    import_entities = [e for e in file_entities if e.get("type") == "Import"]
    type_entities = [
        e for e in file_entities
        if e.get("type") in ("Class", "Interface", "Enum")
    ]

    relationships: list[dict[str, Any]] = []
    for type_entity in type_entities:
        for import_entity in import_entities:
            relationships.append({
                "type": "IMPORTS",
                "source": f"{type_entity['type']}:{type_entity.get('qualified_name', type_entity['name'])}",
                "target": f"Import:{import_entity['name']}",
                "properties": {
                    "source_entity": type_entity["name"],
                    "target_entity": import_entity["name"],
                    "file_path": type_entity.get("file_path", ""),
                    "repository": type_entity.get("repository", ""),
                    "module": type_entity.get("module", ""),
                },
            })

    return relationships
