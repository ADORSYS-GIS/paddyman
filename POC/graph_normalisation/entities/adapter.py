"""EntitySourceAdapter — converts shared.models.Entity into EntitySource.

Reads provenance from ``Entity.properties`` using priority-ordered key lists
that handle naming variations across all supported parsers:

- Java parser (``source_parser``, ``repository``, ``module``, …)
- OpenAPI parser (``spec_source``, ``api_title``, …)
- spaCy extractor (``source_parser``, ``repository``, ``module``, …)
- LLM extractor (same convention as spaCy)
- Markdown parser (``source_parser``, ``document``, …)
"""
from __future__ import annotations

import logging

from shared.models import Entity

from .models import EntitySource

logger = logging.getLogger(__name__)

# Priority-ordered keys for each provenance field.
# Earlier keys take precedence over later ones.
_PARSER_KEYS: tuple[str, ...] = ("source_parser", "parser", "extractor")
_REPO_KEYS: tuple[str, ...] = ("repository", "repo", "repo_name")
_MODULE_KEYS: tuple[str, ...] = ("module", "module_name")
_DOC_KEYS: tuple[str, ...] = ("document", "doc_name", "file_name", "api_title")
_PATH_KEYS: tuple[str, ...] = ("file_path", "path", "spec_file", "spec_source")
_VERSION_KEYS: tuple[str, ...] = ("version", "version_tag", "version_source")
_CONFIDENCE_KEYS: tuple[str, ...] = ("confidence", "score")


def _first_str(props: dict, keys: tuple[str, ...]) -> str | None:
    """Return the first non-blank string value found under *keys* in *props*."""
    for k in keys:
        v = props.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return None


def _first_float(
    props: dict,
    keys: tuple[str, ...],
    default: float = 1.0,
) -> float:
    """Return the first valid float in ``[0.0, 1.0]`` found under *keys*."""
    for k in keys:
        v = props.get(k)
        if v is not None:
            try:
                f = float(v)
                if 0.0 <= f <= 1.0:
                    return f
            except (TypeError, ValueError):
                pass
    return default


class EntitySourceAdapter:
    """Convert a :class:`~shared.models.Entity` into an :class:`~models.EntitySource`.

    Works with entities produced by any parser by reading well-known property
    keys.  Unknown keys are ignored; missing values fall back to ``None``.
    """

    def adapt(self, entity: Entity) -> EntitySource:
        """Build an :class:`~models.EntitySource` from *entity*.

        Args:
            entity: Raw entity from any parser or extractor.

        Returns:
            Populated :class:`~models.EntitySource` with full provenance.
        """
        props = entity.properties

        source_parser = (
            _first_str(props, _PARSER_KEYS)
            or entity.source
            or "unknown"
        )

        return EntitySource(
            source_parser=source_parser,
            original_name=entity.name,
            repository=_first_str(props, _REPO_KEYS),
            module=_first_str(props, _MODULE_KEYS),
            document=_first_str(props, _DOC_KEYS),
            file_path=_first_str(props, _PATH_KEYS),
            version_tag=_first_str(props, _VERSION_KEYS),
            confidence=_first_float(props, _CONFIDENCE_KEYS),
            entity_ref=entity,
        )
