"""spaCy custom pipeline components for the entity extraction pipeline.

Each component is a plain callable that accepts and returns a
:class:`spacy.tokens.Doc`.  They are registered as spaCy factories so they
can be added with ``nlp.add_pipe(component_name)``.

Currently defined:
- ``version_tagger`` — re-exported from :mod:`pipeline.version_tagger` for
  uniform discovery; the factory is registered on import of that module.
"""
from __future__ import annotations

# Import triggers the @Language.factory registration side-effect.
from pipeline.version_tagger import VersionTaggerComponent, derive_version_tag  # noqa: F401

__all__ = [
    "VersionTaggerComponent",
    "derive_version_tag",
]
