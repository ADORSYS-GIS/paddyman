"""Annotation helper functions for spring_bean_relationship_builder."""
from __future__ import annotations

from typing import Any

_INJECT_ANN = {"@Autowired", "@Inject", "@Resource"}
_QUAL_ANN = {"@Qualifier", "@Named"}


def ann_name(ann: dict[str, Any]) -> str:
    return str(ann.get("name", ""))


def ann_attr(ann: dict[str, Any], key: str) -> Any:
    attrs = ann.get("attributes", {})
    return attrs.get(key) if isinstance(attrs, dict) else None


def as_bool(value: Any, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() != "false"
    return default


def inject_meta(annotations: list[dict[str, Any]]) -> tuple[str | None, bool]:
    for ann in annotations:
        name = ann_name(ann)
        if name in _INJECT_ANN:
            if name == "@Autowired":
                return name, as_bool(ann_attr(ann, "required"), True)
            return name, True
    return None, True


def qualifier_meta(annotations: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    for ann in annotations:
        name = ann_name(ann)
        if name in _QUAL_ANN:
            bean = ann_attr(ann, "value") or ann_attr(ann, "name")
            return name if bean is None else f'{name}("{bean}")', str(bean) if bean else None
        if name == "@Resource":
            bean = ann_attr(ann, "name")
            return name if bean is None else f'{name}("{bean}")', str(bean) if bean else None
    return None, None
