"""Adapters for parser and extractor relationship outputs."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from shared.models import Relationship

from .models import RawRelationship


def adapt_relationship(raw: Any) -> RawRelationship:
    """Adapt *raw* into :class:`RawRelationship`.

    Supports dicts, parser dataclasses, GLM triples, and shared
    :class:`~shared.models.Relationship` instances.
    """
    if isinstance(raw, RawRelationship):
        return raw
    if isinstance(raw, Relationship):
        return _from_shared(raw)
    data = _as_mapping(raw)
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    parser = _first(data, ("source_parser", "parser", "extractor"), metadata)
    return RawRelationship(
        source=_first(data, ("source", "subject", "subject_name", "source_entity_id")),
        target=_first(data, ("target", "object_name", "object", "target_entity_id")),
        relationship_type=_first(data, ("relationship", "relationship_type", "type", "predicate")),
        source_parser=parser or _infer_parser(data),
        repository=_first(data, ("repository",), metadata),
        module=_first(data, ("module",), metadata),
        document=_first(data, ("document", "source_document"), metadata),
        file_path=_first(data, ("file_path", "spec_source"), metadata),
        version_tag=_first(data, ("version_tag", "version"), metadata),
        confidence=_confidence(data),
        provenance={"raw": data},
    )


def _from_shared(rel: Relationship) -> RawRelationship:
    props = rel.properties
    return RawRelationship(
        source=str(props.get("source") or rel.source_entity_id),
        target=str(props.get("target") or rel.target_entity_id),
        relationship_type=str(props.get("original_type") or rel.type),
        source_parser=str(props.get("source_parser") or "shared_model"),
        repository=_string(props.get("repository")),
        module=_string(props.get("module")),
        document=_string(props.get("document")),
        file_path=_string(props.get("file_path")),
        version_tag=_string(props.get("version_tag")),
        confidence=rel.confidence,
        provenance={"relationship_id": str(rel.id), "properties": props},
    )


def _as_mapping(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    if is_dataclass(raw):
        return asdict(raw)
    return dict(vars(raw))


def _first(data: dict[str, Any], keys: tuple[str, ...], extra: dict | None = None) -> str:
    for source in (data, extra or {}):
        for key in keys:
            value = source.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
    return ""


def _string(value: Any) -> str | None:
    return str(value).strip() if value is not None and str(value).strip() else None


def _confidence(data: dict[str, Any]) -> float:
    try:
        value = float(data.get("confidence", 1.0))
        return value if 0.0 <= value <= 1.0 else 1.0
    except (TypeError, ValueError):
        return 1.0


def _infer_parser(data: dict[str, Any]) -> str:
    """Infer source parser for common parser output shapes."""
    if "spec_source" in data or "ref_path" in data:
        return "openapi_parser"
    file_path = str(data.get("file_path", ""))
    if "relationship_type" in data and ("package" in data or file_path.endswith(".java")):
        return "java_parser"
    if "predicate" in data or "object_name" in data:
        return "glm_triple_extractor"
    return "unknown"