"""Canonical document id factory and normalization helpers.

Provide a single place to compute stable, canonical `document_id` values
used throughout parser outputs and by the aggregator. The factory aims to
produce deterministic identifiers of the form:

    {parser}:{repository_or_bundle}:{relative_path}

For single-file specs the factory returns a two-segment id:

    {parser}:{sanitized_filename}

The module also exports `normalize_document_id()` to migrate older formats
that used a single colon followed by a filesystem-like path (e.g.
`openapi_parser:specs/foo.yaml`).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional
from uuid import uuid5, NAMESPACE_URL, UUID as _UUID


def _sanitize_segment(value: str) -> str:
    s = str(value).strip()
    # allow alnum, dots, dash and underscore; map everything else to underscore
    return "".join(c if c.isalnum() or c in {"-", "_", "."} else "_" for c in s)


def make_document_id(source_parser: str, repo: Optional[str], root: Path, file_path: Path) -> str:
    """Create a canonical document id.

    Args:
        source_parser: parser short name (e.g. "java_parser").
        repo: repository or bundle identifier (may include additional
            colon-separated parts, e.g. "repo:module"). If ``None`` the
            repository is inferred from the first path segment under ``root``.
        root: directory considered the root for the collection (used to
            compute relative paths and to infer repository names).
        file_path: absolute path to the file for which to build an id.

    Returns:
        Canonical document id string.
    """
    try:
        rel = file_path.relative_to(root).as_posix()
    except Exception:
        # Fall back to best-effort path formatting
        rel = file_path.as_posix()

    # Normalise repeated slashes
    rel = rel.replace("//", "/")

    # If no repo provided try to infer it from the first path component.
    if not repo:
        if "/" in rel:
            repo_part, rel_tail = rel.split("/", 1)
            return f"{source_parser}:{_sanitize_segment(repo_part)}:{rel_tail}"
        # Single-file bundle -> keep it short (parser:filename)
        return f"{source_parser}:{_sanitize_segment(rel)}"

    # Repo provided; allow the caller to pass colon-separated subparts
    # (e.g. "repo:module") which will be preserved in the id.
    repo_parts = [p for p in str(repo).split(":") if p != ""]
    sanitized_parts = [_sanitize_segment(p) for p in repo_parts]

    # Determine the portion of the path that should be treated as the
    # repository-internal relative path. Try to avoid repeating repository
    # or module names twice (many existing formats embed the module name
    # in the relative path).
    rel_tail = rel
    # If the relative path starts with the repository folder, drop it.
    if rel.startswith(repo_parts[0] + "/"):
        rel_tail = rel.split("/", 1)[1]
    # If the caller encoded a module as the last repo part, and the
    # relative path starts with that module, remove the leading module
    # segment to avoid duplication.
    elif len(repo_parts) > 1 and rel.startswith(repo_parts[-1] + "/"):
        rel_tail = rel.split("/", 1)[1]

    # Avoid creating duplicate two-segment ids like "parser:spec.yaml:spec.yaml".
    if ":" not in ":".join(sanitized_parts) and "/" not in rel_tail and sanitized_parts[0] == _sanitize_segment(rel_tail):
        return f"{source_parser}:{sanitized_parts[0]}"

    return f"{source_parser}:{':'.join(sanitized_parts)}:{rel_tail}"


def normalize_document_id(old_id: str) -> str:
    """Attempt to normalise older document id formats.

    Typical legacy format used in some parser outputs was:

        <parser>:<filesystem-like-path>

    (e.g. ``java_parser:repo/module/src/.../File.java``). This helper converts
    the first slash in the remainder into a colon so the result follows the
    canonical ``parser:repo:relative_path`` shape.
    """
    if not old_id:
        return old_id

    s = old_id.replace("\\", "/")
    # collapse repeated slashes and colons
    while "//" in s:
        s = s.replace("//", "/")
    while "::" in s:
        s = s.replace("::", ":")

    if ":" not in s:
        return s

    parser, remainder = s.split(":", 1)
    if "/" in remainder and ":" not in remainder:
        # convert the first slash to a colon
        remainder = remainder.replace("/", ":", 1)
        return f"{parser}:{remainder}"

    return s


def stable_uuid(*components: str, namespace: _UUID = NAMESPACE_URL) -> str:
    """Return a deterministic UUIDv5 string built from the provided components.

    Components are joined with a colon (":") to form the name used to compute
    the UUIDv5. At least one component must be provided.
    """
    if not components:
        raise ValueError("stable_uuid requires at least one component")

    name = ":".join(str(c) for c in components)
    return str(uuid5(namespace, name))
