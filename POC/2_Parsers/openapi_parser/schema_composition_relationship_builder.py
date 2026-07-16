"""Build schema composition relationships (allOf/oneOf/anyOf/not)."""
from __future__ import annotations

from typing import Any
from uuid import uuid4


class SchemaCompositionRelationshipBuilder:
    """Build explicit composition relationships between schema entities."""

    def build(
        self,
        schemas: list[dict[str, Any]],
        schema_index: dict[str, str],
    ) -> list[dict[str, Any]]:
        relationships: list[dict[str, Any]] = []
        for schema in schemas:
            source_id = schema.get("id")
            schema_name = schema.get("name")
            if not source_id or not isinstance(schema_name, str):
                continue

            compositions = schema.get("schema_composition", [])
            if not isinstance(compositions, list):
                continue

            relationships.extend(
                self._relationships_for_schema(
                    source_id=source_id,
                    schema_name=schema_name,
                    compositions=compositions,
                    schema_index=schema_index,
                )
            )
        return relationships

    def _relationships_for_schema(
        self,
        source_id: str,
        schema_name: str,
        compositions: list[dict[str, Any]],
        schema_index: dict[str, str],
    ) -> list[dict[str, Any]]:
        relationships: list[dict[str, Any]] = []
        for descriptor in compositions:
            if not isinstance(descriptor, dict):
                continue
            target_name = descriptor.get("target_schema")
            if not isinstance(target_name, str) or not target_name:
                continue
            target_id = schema_index.get(target_name)
            rel_type = descriptor.get("relationship_type")
            if not target_id or not isinstance(rel_type, str):
                continue
            relationships.append(
                {
                    "id": str(uuid4()),
                    "source_entity_id": source_id,
                    "target_entity_id": target_id,
                    "type": rel_type,
                    "properties": self._relationship_properties(
                        descriptor, schema_name, target_name
                    ),
                    "confidence": 1.0,
                }
            )
        return relationships

    def _relationship_properties(
        self,
        descriptor: dict[str, Any],
        schema_name: str,
        target_name: str,
    ) -> dict[str, Any]:
        props: dict[str, Any] = {
            "composition_type": descriptor.get("composition_type"),
            "schema_name": schema_name,
            "composed_schema": target_name,
        }
        if descriptor.get("position") is not None:
            props["position"] = descriptor.get("position")
        if descriptor.get("discriminator") is not None:
            props["discriminator"] = descriptor.get("discriminator")
        if descriptor.get("ref_path") is not None:
            props["ref_path"] = descriptor.get("ref_path")
        if descriptor.get("path"):
            props["path"] = descriptor.get("path")
        return props
