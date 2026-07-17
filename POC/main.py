"""Top-level compatibility shim used by tests.

Some tests import `run_pipeline` from `main`. Provide a thin re-export
so imports resolve cleanly when running tests from `POC/`.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def _load_graph_main() -> ModuleType | None:
    """Dynamically load `POC/graph_normalisation/main.py` as a module.

    This avoids using an invalid package name at import time (module name
    starts with a digit). Returns the loaded module or None on failure.
    """
    root = Path(__file__).resolve().parent
    candidate = root / "graph_normalisation" / "main.py"
    if not candidate.exists():
        return None
    spec = importlib.util.spec_from_file_location("graph_main", str(candidate))
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return None
    return mod


_mod = _load_graph_main()
if _mod is not None and hasattr(_mod, "run_pipeline"):
    run_pipeline = getattr(_mod, "run_pipeline")
else:  # pragma: no cover - shim for test environments without graph module
    def run_pipeline(*args, **kwargs):
        raise RuntimeError("Graph Normalisation runner not available in this environment")
