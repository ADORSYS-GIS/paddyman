"""Build `MethodCall` entities and a module-level index from CALLS relationships.

This module converts CALLS relationship dicts into explicit `MethodCall`
entity dictionaries and produces a lightweight `method_calls` index for
fast querying by downstream consumers.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, List, Tuple
from uuid import uuid4
from shared.id_factory import stable_uuid, make_document_id


def _read_line_snippet(repo_root: Path, file_path: str, line_no: int) -> str:
    try:
        p = repo_root / file_path
        text = p.read_text(encoding="utf-8")
        lines = text.splitlines()
        if 1 <= line_no <= len(lines):
            return lines[line_no - 1].strip()
    except Exception:
        pass
    return ""


def _call_type_from_props(props: dict[str, Any]) -> str:
    if props.get("is_constructor"):
        return "constructor"
    if props.get("is_static"):
        return "static"
    return "instance"


def build_method_call_entities(
    relationships: Iterable[dict[str, Any]],
    entities: Iterable[dict[str, Any]],
    repo_root: Path,
) -> Tuple[List[dict[str, Any]], List[dict[str, Any]]]:
    """Create MethodCall entities and a compact `method_calls` index.

    Args:
        relationships: Iterable of relationship dicts (as produced by
            `java_relationship_builder`).
        entities: Iterable of existing entity dicts (used for basic context).
        repo_root: Repository root path used to read source snippets.

    Returns:
        A tuple: (list_of_method_call_entities, method_calls_index_list).
    """
    out_entities: list[dict[str, Any]] = []
    index: list[dict[str, Any]] = []

    for rel in relationships:
        if rel.get("type") != "CALLS":
            continue

        props = rel.get("properties", {})
        call_site = props.get("call_site_line") or rel.get("call_site_line")
        start_line = int(call_site) if call_site is not None else None
        end_line = start_line

        caller_uuid = rel.get("source_entity_id")
        callee_uuid = rel.get("target_entity_id")
        callee_qname = rel.get("target")

        call_type = _call_type_from_props(props)

        snippet = ""
        if start_line is not None and rel.get("file_path"):
            snippet = _read_line_snippet(repo_root, rel.get("file_path"), start_line)

        entity = {
            "type": "MethodCall",
            "uuid": str(uuid4()),
            "caller_uuid": caller_uuid,
            "callee_uuid": callee_uuid,
            "callee_qualified_name": callee_qname,
            "resolved": bool(callee_uuid),
            "file_path": rel.get("file_path"),
            "start_line": start_line,
            "end_line": end_line,
            "call_type": call_type,
            "source_snippet": snippet,
            "properties": {
                "method_signature": props.get("method_signature"),
                "argument_count": props.get("argument_count"),
                "argument_types": props.get("argument_types"),
                "receiver_variable": props.get("receiver_variable"),
            },
            "repository": rel.get("repository"),
            "module": rel.get("module"),
        }

        # Build a stable, compact top-level index entry matching the
        # normalized contract required by downstream consumers.
        # Compute a canonical document id for the source file.
        doc_id = None
        try:
            file_rel = rel.get("file_path") or ""
            repo = rel.get("repository")
            module = rel.get("module")
            if repo:
                repo_param = repo if module in (None, "", ".") or module == repo else f"{repo}:{module}"
            else:
                repo_param = None
            doc_path = repo_root / file_rel if file_rel else repo_root
            doc_id = make_document_id("java_parser", repo_param, repo_root, doc_path)
        except Exception:
            doc_id = None

        caller_context = rel.get("source")
        callee_name = rel.get("target_method") or ""
        callee_fqn = rel.get("target") or None
        arg_types = props.get("argument_types") or []

        index_item = {
            "id": stable_uuid(
                "MethodCall",
                str(rel.get("repository") or ""),
                str(rel.get("module") or ""),
                str(rel.get("file_path") or ""),
                str(start_line or ""),
                str(callee_name or ""),
                str(caller_context or ""),
            ),
            "source": doc_id,
            "caller_context": caller_context,
            "callee_name": callee_name,
            "callee_fqn": callee_fqn,
            "argument_types": list(arg_types),
            "location": {"path": str(repo_root / rel.get("file_path")) if rel.get("file_path") else "", "start_line": start_line, "end_line": end_line},
            "resolved": bool(callee_uuid),
            "call_type": call_type,
        }

        out_entities.append(entity)
        index.append(index_item)

    return out_entities, index
