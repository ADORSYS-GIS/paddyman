"""Parser for Java ``.properties`` files.

Handles the standard Java properties syntax including:
- ``key=value``, ``key: value``, and whitespace-separated ``key value`` forms.
- Line continuation with a trailing backslash.
- Comment lines starting with ``#`` or ``!``.
- Blank lines.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _parse_content(text: str) -> dict[str, str]:
    """Parse a properties file body into an ordered key/value mapping.

    Args:
        text: Raw file content.

    Returns:
        Dictionary of all key/value pairs found in *text*.
    """
    props: dict[str, str] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # Join continuation lines (trailing backslash)
        while line.endswith("\\") and i + 1 < len(lines):
            line = line[:-1] + lines[i + 1].lstrip()
            i += 1
        i += 1

        stripped = line.strip()
        if not stripped or stripped[0] in ("#", "!"):
            continue

        # Split on the first ``=`` or ``:`` delimiter
        for sep in ("=", ":"):
            if sep in stripped:
                key, _, value = stripped.partition(sep)
                props[key.strip()] = value.strip()
                break
        else:
            # Key-only entry (no delimiter found)
            props[stripped] = ""

    return props


def parse_properties_file(path: Path) -> tuple[dict[str, str], list[str]]:
    """Read and parse a ``.properties`` file.

    Args:
        path: Absolute path to the file.

    Returns:
        ``(key_value_dict, error_list)`` — the error list is empty on success.
    """
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        errors.append(f"Cannot read {path}: {exc}")
        return {}, errors
    return _parse_content(text), errors
