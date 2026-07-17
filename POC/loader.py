"""Top-level loader shim for tests.

Re-exports the extraction loader implementation from
`extractors/loader.py` so bare `import loader` resolves to the
expected API regardless of sys.path ordering.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

_impl_path = Path(__file__).resolve().parent / "extractors" / "loader.py"
if _impl_path.exists():
    spec = importlib.util.spec_from_file_location("_extractors_loader_impl", str(_impl_path))
    _mod = importlib.util.module_from_spec(spec)
    # Ensure the module is present in sys.modules so decorators and
    # runtime introspection that rely on module lookups work correctly.
    if spec and spec.loader:
        sys.modules[spec.name] = _mod
        spec.loader.exec_module(_mod)
    # Re-export public API
    for _name in ("ExtractionRecord", "load_all_records", "load_normalized_records", "load_markdown_records", "load_openapi_records", "load_java_records"):
        if hasattr(_mod, _name):
            globals()[_name] = getattr(_mod, _name)
else:  # pragma: no cover - fallback for environments without extractors
    raise ImportError("Embedded loader implementation not found: expected extractors/loader.py")
