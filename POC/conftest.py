"""Root conftest — runs before any test collection.

Adds all extractor sub-package roots to sys.path so integration tests can
import from ``embeddings``, ``llm``, and ``spacy`` extractor modules without
triggering the ``client`` / ``services`` namespace conflict.
"""
from __future__ import annotations

import sys
from pathlib import Path

_poc_root = str(Path(__file__).resolve().parent)

# Pre-import the real spaCy library before 3_Extractors/ is on sys.path.
# This locks it into sys.modules so the project-local 3_Extractors/spacy/
# directory (which shares the name) never shadows the installed package.
import spacy as _real_spacy  # noqa: F401

_spacy_root = str(Path(_poc_root) / "3_Extractors" / "spacy")
_extractors_root = str(Path(_poc_root) / "3_Extractors")
_embed_root = str(Path(_poc_root) / "3_Extractors" / "embeddings")
_llm_root = str(Path(_poc_root) / "3_Extractors" / "llm")

# Insert in reverse order so llm ends at position 0 (highest priority),
# ensuring `from client.base_client import LLMClientError` resolves to the
# LLM client — the same one ExtractionService imports and whose exceptions
# it catches.
for _p in (_spacy_root, _extractors_root, _embed_root, _llm_root):
    if _p not in sys.path:
        sys.path.insert(0, _p)
