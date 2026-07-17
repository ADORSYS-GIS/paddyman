"""Simple YAML key-line indexer for OpenAPI specs.

This lightweight indexer walks the YAML text and records the start/end
line numbers for mapping keys. It's indentation-based and intended for
parser-time heuristics (operation/component source locations). It's not a
full YAML parser but works well for typical OpenAPI layouts.
"""
from __future__ import annotations

from typing import Any


def _clean_key(raw: str) -> str:
    key = raw.split(":", 1)[0].strip()
    if (key.startswith("\"") and key.endswith("\"")) or (key.startswith("'") and key.endswith("'")):
        return key[1:-1]
    return key


def build_index(text: str) -> dict[str, Any]:
    """Build an index mapping YAML paths to (start_line, end_line).

    Returns a dict with keys:
      - 'paths': {(path, method): (start, end)}
      - 'components': {comp_type: {name: (start, end)}}
    """
    lines = text.splitlines()
    stack: list[dict[str, Any]] = []
    node_ranges: dict[tuple[str, ...], dict[str, int]] = {}

    for lineno, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        stripped = raw.lstrip()
        indent = len(raw) - len(stripped)

        # Only consider mapping keys (contain ':'), skip flow-style values
        if ":" not in stripped:
            continue

        key = _clean_key(stripped)

        # Pop stack when current indent <= top indent
        while stack and indent <= stack[-1]["indent"]:
            node = stack.pop()
            path = tuple(node["path"])
            if path not in node_ranges:
                node_ranges[path] = {"start": node["start"], "end": lineno - 1}

        parent_path = stack[-1]["path"] if stack else []
        new_path = [*parent_path, key]
        stack.append({"indent": indent, "key": key, "path": new_path, "start": lineno})

    last_line = len(lines)
    while stack:
        node = stack.pop()
        path = tuple(node["path"])
        if path not in node_ranges:
            node_ranges[path] = {"start": node["start"], "end": last_line}

    # Build friendly indexes
    paths_index: dict[tuple[str, str], tuple[int, int]] = {}
    components_index: dict[str, dict[str, tuple[int, int]]] = {
        "requestBodies": {},
        "responses": {},
        "parameters": {},
        "schemas": {},
        "securitySchemes": {},
        "tags": {},
    }

    for path_tuple, rng in node_ranges.items():
        if not path_tuple:
            continue
        if path_tuple[0] == "paths" and len(path_tuple) >= 3:
            p = path_tuple[1]
            m = path_tuple[2]
            paths_index[(p, m.upper())] = (rng["start"], rng["end"])
        if path_tuple[0] == "components" and len(path_tuple) >= 3:
            comp = path_tuple[1]
            name = path_tuple[2]
            if comp in components_index:
                components_index[comp][name] = (rng["start"], rng["end"])
        # (Deprecated) previous attempt to index top-level `tags` entries was
        # incomplete. We'll handle top-level `tags` blocks below via a
        # line-oriented scan to map each tag `name` to a start/end range.

    # Best-effort: index top-level `tags` list items by scanning the YAML
    # text for a `tags:` block and extracting `name:` values for each list
    # item. This provides line ranges that can be used to attach provenance
    # information to Tag entities.
    try:
        lines = text.splitlines()
        for lineno, raw in enumerate(lines, start=1):
            if not raw.strip():
                continue
            stripped = raw.lstrip()
            if not stripped.startswith("tags:"):
                continue
            tags_indent = len(raw) - len(stripped)
            # Walk subsequent lines belonging to the tags block
            i = lineno + 1
            current_block_start = None
            blocks: list[tuple[int, int]] = []
            while i <= len(lines):
                line = lines[i - 1]
                if not line.strip():
                    i += 1
                    continue
                indent = len(line) - len(line.lstrip())
                if indent <= tags_indent:
                    break
                s = line.lstrip()
                # Start of a new list item
                if s.startswith("-") or s.startswith("- "):
                    if current_block_start is not None:
                        blocks.append((current_block_start, i - 1))
                    current_block_start = i
                i += 1
            if current_block_start is not None:
                blocks.append((current_block_start, i - 1))

            for start, end in blocks:
                tag_name = None
                for j in range(start, end + 1):
                    ln = lines[j - 1].lstrip()
                    if ln.startswith("name:"):
                        val = ln.split(":", 1)[1].strip()
                        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                            val = val[1:-1]
                        tag_name = val
                        break
                if tag_name:
                    components_index.setdefault("tags", {})[tag_name] = (start, end)
    except Exception:
        # Indexing is best-effort; don't fail on parsing issues
        pass

    return {"paths": paths_index, "components": components_index}
