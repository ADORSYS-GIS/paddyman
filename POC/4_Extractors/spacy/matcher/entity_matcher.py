"""spaCy EntityRuler-backed entity matcher for domain vocabulary.

The matcher is injected into the spaCy pipeline as the ``entity_ruler``
component so that domain terms are resolved to ``DOMAIN_ENTITY`` spans before
the version-tag injection stage runs.
"""
from __future__ import annotations

import logging
from typing import Any

import spacy
from spacy.language import Language

from vocabulary import VocabularyEntry, build_entity_ruler_patterns

logger = logging.getLogger(__name__)

_COMPONENT_NAME = "domain_entity_ruler"


def add_entity_matcher(
    nlp: Language,
    entries: list[VocabularyEntry] | None = None,
) -> Language:
    """Add a domain ``EntityRuler`` component to *nlp* and return it.

    The ruler is inserted **before** the ``ner`` component when one exists,
    otherwise it is appended.  Calling this function on the same *nlp*
    instance twice raises :class:`ValueError` (spaCy prevents duplicate
    component names).

    Args:
        nlp:     spaCy Language pipeline to extend.
        entries: Domain vocabulary to match. Defaults to the built-in set.

    Returns:
        The mutated *nlp* instance (same object, returned for chaining).
    """
    patterns = build_entity_ruler_patterns(entries)

    ruler_config: dict[str, Any] = {"overwrite_ents": True}

    if "ner" in nlp.pipe_names:
        ruler = nlp.add_pipe(
            "entity_ruler",
            name=_COMPONENT_NAME,
            before="ner",
            config=ruler_config,
        )
    else:
        ruler = nlp.add_pipe(
            "entity_ruler",
            name=_COMPONENT_NAME,
            config=ruler_config,
        )

    ruler.add_patterns(patterns)  # type: ignore[union-attr]
    logger.debug(
        "EntityRuler '%s' added with %d patterns", _COMPONENT_NAME, len(patterns)
    )
    return nlp
