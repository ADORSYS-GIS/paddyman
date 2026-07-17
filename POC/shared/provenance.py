"""Canonical provenance helper utilities.

Provide a small helper to ensure parser/writer provenance dictionaries
contain the minimal canonical keys (`path` and `stage`) and optionally
`parser`/`module` when available. Parsers and writers should call
`ensure_provenance` before emitting documents or bundle-level provenance
to guarantee downstream consumers can reliably locate source files.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union
from typing import Tuple


def ensure_provenance(
    existing: Optional[Dict[str, Any]] = None,
    file_path: Optional[Union[Path, str]] = None,
    stage: Optional[str] = None,
    parser: Optional[str] = None,
    module: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a canonical provenance dict.

    - Guarantees `path` when a file path or a common alias is available.
    - Ensures `stage` is present when provided.
    - Preserves any additional keys supplied in *existing*.

    The function prefers existing values but will populate missing
    canonical keys from provided arguments.
    """
    prov: Dict[str, Any] = dict(existing or {})

    # If a canonical 'path' is missing, map common aliases -> 'path'
    if not prov.get("path"):
        for alias in ("file", "file_path", "source_file", "source_path", "source", "specification"):
            v = prov.get(alias)
            if v:
                prov["path"] = v
                break

    # If still missing, use explicit file_path argument
    if not prov.get("path") and file_path is not None:
        try:
            prov["path"] = str(Path(file_path).resolve())
        except Exception:
            prov["path"] = str(file_path)

    # Populate stage/parser/module if provided and absent
    if stage and not prov.get("stage"):
        prov["stage"] = stage
    if parser and not prov.get("parser"):
        prov["parser"] = parser
    if module and not prov.get("module"):
        prov["module"] = module

    return prov


def normalize_paths(source_meta: dict[str, Any], root: Path | None = None) -> dict[str, Any]:
    """Normalize path-like fields in a parser `source_metadata` dict.

    Ensures the canonical keys exist with the following semantics:
    - `path`: absolute filesystem path (preferred for provenance)
    - `location`: same as `path` (kept for `SourceMetadata.location` compatibility)
    - `relative_path`: path relative to repository or spec root when available
    - `file_name`: base filename

    The function mutates a shallow copy of *source_meta* and returns it.
    If *root* is provided, `relative_path` is computed relative to it when possible.
    """
    meta = dict(source_meta or {})

    # Prefer explicit keys
    file_path = meta.get("file_path") or meta.get("path") or meta.get("file") or meta.get("location")
    relative = meta.get("relative_path") or meta.get("relative")

    # Compute absolute path when possible
    abs_path = None
    if file_path:
        try:
            abs_path = str(Path(file_path).resolve())
        except Exception:
            abs_path = str(file_path)

    # Derive file_name
    if not meta.get("file_name") and abs_path:
        meta["file_name"] = Path(abs_path).name

    # Compute relative_path if root provided and not present
    if not relative and abs_path and root is not None:
        try:
            rel = Path(abs_path).relative_to(root)
            meta.setdefault("relative_path", str(rel.as_posix()))
        except Exception:
            pass

    # Ensure canonical `path` and `location`
    if abs_path:
        meta.setdefault("path", abs_path)
        meta.setdefault("location", abs_path)
    elif relative:
        meta.setdefault("relative_path", relative)
        meta.setdefault("location", relative)

    return meta
