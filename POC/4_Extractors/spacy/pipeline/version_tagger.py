"""Version-tag injection component for the spaCy extraction pipeline.

Derives a version tag deterministically using a three-level priority chain:

1. **Metadata** — explicit ``version`` / ``api_version`` field supplied by a
   parser (highest priority).
2. **Source path** — ``file_path``, ``module``, or ``repository`` segments
   matched against structural version patterns.
3. **Content** — result produced by the upstream ``content_version_extractor``
   component (lowest priority).

Both the resolved tag and its source label are stored in ``doc.user_data`` for
every matched entity span and consumed by the converter when building
:class:`~shared.models.Entity` objects.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from spacy.language import Language
from spacy.tokens import Doc

logger = logging.getLogger(__name__)

_COMPONENT_NAME = "version_tagger"

# Path/module/repository structural patterns (priority 2).
_PATH_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bv(\d+(?:\.\d+)*)\b", re.IGNORECASE),        # v1, v1.2, V3
    re.compile(r"_(\d+)_(\d+)(?:_(\d+))?(?:\b|_|$)"),          # _1_0, _1_0_1
    re.compile(r"[-/](\d+)\.(\d+)(?:\.(\d+))?(?:\b|[-/_]|$)"), # -1.0, /1.2.3
    re.compile(r"\b(\d+)_(\d+)\b"),                             # 1_0
]


def _extract_version_from_string(text: str) -> str | None:
    for pattern in _PATH_PATTERNS:
        m = pattern.search(text)
        if m is None:
            continue
        groups = [g for g in m.groups() if g is not None]
        if groups:
            return "v" + ".".join(groups)
    return None


def derive_version_with_source(
    metadata: dict[str, Any],
    content_version: dict[str, Any] | None = None,
) -> tuple[str | None, str | None]:
    """Return ``(version_tag, source_label)`` using the 3-level priority chain.

    Args:
        metadata:        Source-metadata dict (from ``doc.user_data``).
        content_version: Result from ``content_version_extractor``, e.g.
                         ``{"version": "v1.3", "rule": "psd2"}``.

    Returns:
        A two-tuple ``(version, source)`` where *source* is one of
        ``"metadata"``, ``"source_path"``, ``"content:<rule>"`` or ``None``.
    """
    # Priority 1 — explicit metadata field.
    explicit: str | None = metadata.get("version") or metadata.get("api_version")
    if explicit:
        cleaned = str(explicit).strip().lstrip("vV")
        if cleaned:
            return "v" + cleaned, "metadata"

    # Priority 2 — structural path / module / repository.
    for key in ("file_path", "module", "repository"):
        value: str | None = metadata.get(key)
        if value:
            tag = _extract_version_from_string(str(value))
            if tag:
                return tag, "source_path"

    # Priority 3 — content extracted by upstream component.
    if content_version:
        v: str | None = content_version.get("version")
        if v:
            rule = content_version.get("rule", "unknown")
            return v, f"content:{rule}"

    return None, None


def derive_version_tag(metadata: dict[str, Any]) -> str | None:
    """Backward-compatible helper — returns version tag only.

    Considers only priority-1 and priority-2 sources (no content).
    """
    version, _ = derive_version_with_source(metadata)
    return version


@Language.factory(_COMPONENT_NAME)
def _create_version_tagger(nlp: Language, name: str) -> "VersionTaggerComponent":  # noqa: ARG001
    """spaCy factory for :class:`VersionTaggerComponent`."""
    return VersionTaggerComponent()


class VersionTaggerComponent:
    """Inject version tags and source labels into ``doc.user_data``.

    Reads ``doc.user_data["source_metadata"]`` and
    ``doc.user_data["content_version"]``, resolves a version tag per entity
    via :func:`derive_version_with_source`, and writes results to
    ``doc.user_data["version_tags"]`` and ``doc.user_data["version_sources"]``.
    """

    def __call__(self, doc: Doc) -> Doc:
        source_meta: dict[str, Any] = doc.user_data.get("source_metadata", {})
        content_version: dict[str, Any] | None = doc.user_data.get("content_version")

        doc.user_data.setdefault("version_tags", {})
        doc.user_data.setdefault("version_sources", {})

        for ent in doc.ents:
            version, source = derive_version_with_source(source_meta, content_version)
            doc.user_data["version_tags"][ent.start] = version
            doc.user_data["version_sources"][ent.start] = source
            logger.debug(
                "Version '%s' (source: %s) → entity '%s'",
                version,
                source,
                ent.text,
            )

        return doc
