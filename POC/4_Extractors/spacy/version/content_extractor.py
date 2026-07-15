"""spaCy pipeline component for content-based version extraction.

Scans the full document text using :data:`~version.rules.CONTENT_RULES` and
stores the first match in ``doc.user_data["content_version"]`` as::

    {"version": "v1.3.16", "rule": "psd2"}

This is consumed by :class:`~pipeline.version_tagger.VersionTaggerComponent`
as the priority-3 fallback when no version can be derived from metadata or
source paths.

The component does **not** modify ``doc.ents``; it only enriches
``doc.user_data``.
"""
from __future__ import annotations

import logging
from typing import Any

from spacy.language import Language
from spacy.tokens import Doc

from version.rules import CONTENT_RULES, VersionRule

logger = logging.getLogger(__name__)

_COMPONENT_NAME = "content_version_extractor"


@Language.factory(_COMPONENT_NAME)
def _create_content_version_extractor(
    nlp: Language, name: str  # noqa: ARG001
) -> "ContentVersionExtractorComponent":
    """spaCy factory for :class:`ContentVersionExtractorComponent`."""
    return ContentVersionExtractorComponent()


class ContentVersionExtractorComponent:
    """Scan document text for version patterns and store the best match.

    The component applies :data:`~version.rules.CONTENT_RULES` in order and
    stores only the first (highest-priority) match found.

    Args:
        rules: Override the default rule list (useful in tests).
    """

    def __init__(self, rules: list[VersionRule] | None = None) -> None:
        self._rules: list[VersionRule] = (
            rules if rules is not None else CONTENT_RULES
        )

    def __call__(self, doc: Doc) -> Doc:
        result = self._extract(doc.text)
        doc.user_data["content_version"] = result
        if result:
            logger.debug(
                "Content version '%s' detected by rule '%s'",
                result["version"],
                result["rule"],
            )
        return doc

    def _extract(self, text: str) -> dict[str, Any] | None:
        for rule in self._rules:
            version = rule.extract(text)
            if version:
                return {"version": version, "rule": rule.name}
        return None
