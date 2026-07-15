"""Shared fixtures for graph normalisation runner tests."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_GRAPH_ROOT = _HERE.parent
_POC_ROOT = _HERE.parents[1]

for _p in (str(_POC_ROOT), str(_GRAPH_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)