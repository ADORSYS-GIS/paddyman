"""Parse and validate LLM JSON responses into shared model objects.

Design principles:
- Never raises — all errors land in :class:`~shared.models.ExtractionResult`.
- JSON embedded in markdown fences is extracted before parsing.
- Structural errors are logged and added as warnings or errors.
- Relationships with unresolvable entity names are skipped with a warning.
"""
from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

_poc_root = str(Path(__file__).resolve().parents[3])
if _poc_root not in sys.path:
    sys.path.insert(0, _poc_root)

from shared.models import (
    Entity,
    ExtractionResult,
    ExtractionStatus,
    Relationship,
    SourceMetadata,
)

logger = logging.getLogger(__name__)

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def _unwrap_fences(text: str) -> str:
    """Strip markdown code fences if present."""
    m = _FENCE_RE.search(text)
    return m.group(1).strip() if m else text.strip()


class ResponseParser:
    """Convert raw LLM text into an :class:`~shared.models.ExtractionResult`."""

    def parse(
        self,
        raw: str,
        source_metadata: SourceMetadata,
        source_parser: str | None = None,
    ) -> ExtractionResult:
        """Parse *raw* LLM output into an :class:`ExtractionResult`.

        Returns a ``FAILED`` result (with errors) on unrecoverable JSON
        problems, or a ``SUCCESS`` / ``PARTIAL`` result otherwise.
        """
        warnings: list[str] = []
        errors: list[str] = []

        data = self._load_json(raw, errors)
        if data is None:
            return ExtractionResult(
                source=source_metadata,
                status=ExtractionStatus.FAILED,
                errors=errors,
            )

        entities = self._build_entities(
            data.get("entities", []), source_metadata, source_parser, warnings
        )
        name_index: dict[str, UUID] = {e.name.lower(): e.id for e in entities}
        relationships = self._build_relationships(
            data.get("relationships", []), name_index, warnings
        )

        status = (
            ExtractionStatus.SUCCESS
            if entities or relationships
            else ExtractionStatus.PARTIAL
        )
        return ExtractionResult(
            source=source_metadata,
            entities=entities,
            relationships=relationships,
            status=status,
            warnings=warnings,
            errors=errors,
        )

    # ------------------------------------------------------------------

    def _load_json(
        self, raw: str, errors: list[str]
    ) -> dict[str, Any] | None:
        cleaned = _unwrap_fences(raw)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            errors.append(f"JSON decode error: {exc}")
            logger.warning("LLM returned invalid JSON: %s", exc)
            return None
        if not isinstance(data, dict):
            errors.append(f"Expected JSON object, got {type(data).__name__}")
            return None
        return data

    def _build_entities(
        self,
        items: list[Any],
        source_metadata: SourceMetadata,
        source_parser: str | None,
        warnings: list[str],
    ) -> list[Entity]:
        entities: list[Entity] = []
        for item in items:
            if not isinstance(item, dict):
                warnings.append(f"Skipped non-dict entity: {item!r}")
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                warnings.append("Skipped entity with empty name")
                continue
            props: dict[str, Any] = {
                "label": item.get("label") or "UNKNOWN",
                "source_parser": source_parser,
                "extraction_rule": "llm",
                **(item.get("properties") or {}),
            }
            entities.append(
                Entity(
                    type=str(item.get("type") or "entity"),
                    name=name,
                    source=source_metadata.source_id,
                    properties=props,
                )
            )
        return entities

    def _build_relationships(
        self,
        items: list[Any],
        name_index: dict[str, UUID],
        warnings: list[str],
    ) -> list[Relationship]:
        rels: list[Relationship] = []
        for item in items:
            if not isinstance(item, dict):
                warnings.append(f"Skipped non-dict relationship: {item!r}")
                continue
            src = str(item.get("source") or "").strip().lower()
            tgt = str(item.get("target") or "").strip().lower()
            rel_type = str(item.get("type") or "").strip()
            if not (src and tgt and rel_type):
                warnings.append(f"Skipped incomplete relationship: {item!r}")
                continue
            src_id = name_index.get(src)
            tgt_id = name_index.get(tgt)
            if src_id is None or tgt_id is None:
                missing = src if src_id is None else tgt
                warnings.append(
                    f"Skipped '{rel_type}': unknown entity '{missing}'"
                )
                continue
            confidence = min(max(float(item.get("confidence") or 1.0), 0.0), 1.0)
            rels.append(
                Relationship(
                    source_entity_id=src_id,
                    target_entity_id=tgt_id,
                    type=rel_type,
                    confidence=confidence,
                )
            )
        return rels
