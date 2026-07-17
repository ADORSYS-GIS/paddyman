"""Compatibility shim package for tests.

Some tests import `pipeline.*` as a top-level package. The real
implementation lives under `4_Extractors/spacy/pipeline/`. To avoid
shadowing and sys.path ordering issues during pytest runs, extend this
package's `__path__` to include that directory so submodules like
`pipeline.pipeline` and `pipeline.components` resolve to the project's
implementation files.
"""
from __future__ import annotations

from pathlib import Path
import sys

# Compute the expected path relative to the POC root.
_poc_root = Path(__file__).resolve().parent.parent
_spacy_pipeline = _poc_root / "4_Extractors" / "spacy" / "pipeline"
if _spacy_pipeline.exists():
    __path__.insert(0, str(_spacy_pipeline))
