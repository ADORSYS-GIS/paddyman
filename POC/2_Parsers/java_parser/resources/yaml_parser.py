"""Parser for YAML resource files (``.yml`` / ``.yaml``).

Uses :mod:`yaml` (PyYAML) with a custom safe loader that:

- Silently drops unknown tags (e.g. GitLab CI ``!reference``).
- Loads multi-document streams (Spring Boot ``---`` profile separators)
  by merging all documents into a single mapping.
- Skips Go-template files (Helm charts containing ``{{``) without error.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ── Custom loader: ignore unknown YAML tags ────────────────────────────────────


class _TolerantLoader(yaml.SafeLoader):
    """SafeLoader that silently ignores any unrecognised tag."""


# Catch-all multi-constructor: unknown tags resolve to None / scalar text.
_TolerantLoader.add_multi_constructor(
    "",
    lambda loader, tag_suffix, node: loader.construct_scalar(node)
    if isinstance(node, yaml.ScalarNode)
    else None,
)

# ── Helpers ────────────────────────────────────────────────────────────────────


def _is_go_template(text: str) -> bool:
    """Return ``True`` when *text* looks like a Helm / Go template."""
    stripped = text.lstrip()
    return stripped.startswith("{{") or "{{\n" in text or "{{-" in text


def _load_all_docs(text: str) -> tuple[Any, list[str]]:
    """Load all YAML documents in *text* and merge them.

    For single-document files this is identical to ``safe_load``.
    For multi-document files (``---`` separators, e.g. Spring Boot
    ``application.yml`` with profile overrides) all mapping documents are
    shallow-merged (later docs win on key collision).

    Returns:
        (merged_data, error_list) — error list is empty on success.
    """
    errors: list[str] = []
    try:
        docs = list(yaml.load_all(text, Loader=_TolerantLoader))  # noqa: S506
    except yaml.YAMLError as exc:
        errors.append(str(exc))
        return {}, errors

    valid = [d for d in docs if d is not None]
    if not valid:
        return {}, errors
    if len(valid) == 1:
        return valid[0], errors

    # Merge all mapping documents; non-mapping docs are ignored.
    merged: dict[str, Any] = {}
    for doc in valid:
        if isinstance(doc, dict):
            merged.update(doc)
    return merged or valid[0], errors



def _flatten(data: Any, prefix: str = "", sep: str = ".") -> dict[str, Any]:
    """Flatten a nested mapping/sequence into dot-separated key paths.

    Sequence items are indexed numerically: ``key.0.field``.
    Scalar leaves are kept as-is.

    Args:
        data:   Parsed YAML value (dict, list, or scalar).
        prefix: Current key prefix (empty at top level).
        sep:    Separator between path segments.

    Returns:
        Flat dictionary mapping dot-notation keys to scalar values.
    """
    result: dict[str, Any] = {}
    if isinstance(data, dict):
        for k, v in data.items():
            full_key = f"{prefix}{sep}{k}" if prefix else str(k)
            result.update(_flatten(v, full_key, sep))
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            full_key = f"{prefix}{sep}{idx}" if prefix else str(idx)
            result.update(_flatten(item, full_key, sep))
    else:
        result[prefix] = data
    return result


def parse_yaml_file(path: Path) -> tuple[dict[str, Any], list[str]]:
    """Read and parse a YAML file.

    Handles:

    - **Unknown tags** (e.g. ``!reference`` in GitLab CI files): silently
      treated as scalar or ``None``.
    - **Multi-document streams** (``---`` separators): all mapping documents
      are merged; useful for Spring Boot profile-annotated ``application.yml``.
    - **Go/Helm templates** (files containing ``{{``): skipped without error,
      returning an empty result.

    Args:
        path: Absolute path to the file.

    Returns:
        ``(content_dict, error_list)`` where *content_dict* contains:

        - ``"raw"``: the full parsed tree (merged dict).
        - ``"flat"``: a dot-notation flattened dict.

        The error list is empty on success.
    """
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        errors.append(f"Cannot read {path}: {exc}")
        return {}, errors

    if _is_go_template(text):
        logger.debug("Skipping Go/Helm template: %s", path.name)
        return {"raw": {}, "flat": {}}, []

    data, load_errors = _load_all_docs(text)
    if load_errors:
        for msg in load_errors:
            errors.append(f"YAML parse error in {path}: {msg}")
        return {}, errors

    if data is None:
        data = {}
    flat: dict[str, Any] = _flatten(data) if isinstance(data, dict) else {}
    return {"raw": data, "flat": flat}, errors
