"""Build INJECTS_BEAN relationships from extracted Java entities."""
from __future__ import annotations

from typing import Any

from java_parser.spring_bean_annotation_helpers import (
    ann_attr,
    ann_name,
    inject_meta,
    qualifier_meta,
)

_STEREO_ANN = {"@Component", "@Service", "@Repository", "@Controller", "@RestController"}


def _bean_indices(entities: list[dict[str, Any]]) -> tuple[dict[str, str], dict[str, str], dict[str, bool]]:
    by_type: dict[str, str] = {}
    by_name: dict[str, str] = {}
    by_primary: dict[str, bool] = {}
    for e in entities:
        if e.get("type") not in ("Class", "Interface", "Enum"):
            continue
        name = str(e.get("name", ""))
        uuid = str(e.get("uuid", ""))
        if not name or not uuid:
            continue
        by_type[name] = uuid
        anns = e.get("annotations", [])
        if not isinstance(anns, list):
            continue
        for ann in anns:
            if not isinstance(ann, dict):
                continue
            ann_name_value = ann_name(ann)
            if ann_name_value == "@Primary":
                by_primary[uuid] = True
            bean_name = ann_attr(ann, "value") or ann_attr(ann, "name")
            if ann_name_value in _STEREO_ANN | {"@Named", "@Qualifier"} and bean_name:
                by_name[str(bean_name)] = uuid
    return by_type, by_name, by_primary


def _resolve_target_uuid(type_name: str, bean_name: str | None, by_type: dict[str, str], by_name: dict[str, str]) -> tuple[str, bool]:
    if bean_name and bean_name in by_name:
        return by_name[bean_name], True
    if type_name in by_type:
        return by_type[type_name], True
    return type_name, False


def build_injects_bean_relationships(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create INJECTS_BEAN relationships for field, constructor, and setter injection."""
    by_type, by_name, by_primary = _bean_indices(entities)
    class_index = {str(e.get("name", "")): str(e.get("uuid", "")) for e in entities if e.get("type") in ("Class", "Interface", "Enum")}
    params = [e for e in entities if e.get("type") == "Parameter"]
    params_by_method: dict[str, list[dict[str, Any]]] = {}
    for p in params:
        params_by_method.setdefault(str(p.get("method_qualified_name", "")), []).append(p)

    rels: list[dict[str, Any]] = []
    for entity in entities:
        et = entity.get("type")
        if et not in ("Field", "Constructor", "Method"):
            continue
        anns = entity.get("annotations", [])
        if not isinstance(anns, list):
            continue
        annotation, required = inject_meta([a for a in anns if isinstance(a, dict)])
        if not annotation:
            continue

        source_uuid = class_index.get(str(entity.get("class", "")))
        if not source_uuid:
            continue

        targets: list[tuple[str, str | None, int | None, list[dict[str, Any]]]] = []
        if et == "Field":
            targets.append((str(entity.get("field_type", "")).split("<")[0].replace("[]", ""), str(entity.get("name", "")), None, anns))
        else:
            qn = str(entity.get("qualified_class", ""))
            method_name = "<init>" if et == "Constructor" else str(entity.get("name", ""))
            key = f"{qn}.{method_name}" if method_name != "<init>" else f"{qn}.<init>"
            for p in sorted(params_by_method.get(key, []), key=lambda x: int(x.get("position", 0))):
                p_anns = p.get("annotations", [])
                p_ann_list = p_anns if isinstance(p_anns, list) else []
                targets.append((str(p.get("parameter_type", "")).split("<")[0].replace("[]", ""), str(p.get("name", "")), int(p.get("position", 0)), p_ann_list + anns))

        for target_type, name, pos, combined_anns in targets:
            qualifier, bean_name = qualifier_meta([a for a in combined_anns if isinstance(a, dict)])
            target_uuid, resolved = _resolve_target_uuid(target_type, bean_name, by_type, by_name)
            props: dict[str, Any] = {
                "injection_type": "field" if et == "Field" else ("constructor" if et == "Constructor" else "setter"),
                "framework": "spring",
                "annotation": annotation,
                "required": required,
                "qualifier": qualifier,
                "bean_name": bean_name,
                "is_primary": by_primary.get(target_uuid, False),
            }
            if et == "Field":
                props["field_name"] = name
            elif et == "Constructor":
                props["parameter_name"] = name
                props["parameter_position"] = pos
            else:
                props["setter_method"] = str(entity.get("name", ""))
                props["parameter_name"] = name
                props["parameter_position"] = pos

            rel = {
                "type": "INJECTS_BEAN",
                "source": source_uuid,
                "target": target_uuid,
                "source_entity_id": source_uuid,
                "target_entity_id": target_uuid,
                "properties": props,
            }
            if not resolved:
                rel["target_resolved"] = False
            rels.append(rel)
    return rels
