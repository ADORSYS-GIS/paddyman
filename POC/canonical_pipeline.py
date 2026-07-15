"""Canonical end-to-end pipeline runner."""
from __future__ import annotations

import asyncio
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

_POC_ROOT = Path(__file__).resolve().parent
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
_EXTRACTORS_ROOT = _POC_ROOT / "4_Extractors"
_GRAPH_ROOT = _POC_ROOT / "3_Graph_Normalisation"
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT), str(_EXTRACTORS_ROOT), str(_GRAPH_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)


def run_pipeline(graph_writer: Any = None) -> dict[str, Any]:
    """Run shared-configured stages in canonical dependency order."""
    parser_module = importlib.import_module("parser_pipeline")
    extraction_module = _module_from_path("canonical_extraction_main", _EXTRACTORS_ROOT / "main.py")
    embedding_module = importlib.import_module("embeddings.pipeline")
    graph_module = _module_from_path("canonical_graph_main", _GRAPH_ROOT / "main.py")

    parser_summary = parser_module.run_pipeline()
    extraction_summary = extraction_module.run()
    embedding_output = embedding_module.run_pipeline()
    graph_summary = asyncio.run(graph_module.run_pipeline(graph_writer=graph_writer))

    return {
        "parser": parser_summary,
        "extraction": extraction_summary,
        "embeddings": embedding_output,
        "graph": graph_summary,
    }


def _module_from_path(name: str, path: Path):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    run_pipeline()