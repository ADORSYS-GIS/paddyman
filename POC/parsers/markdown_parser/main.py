"""Orchestrator for the Markdown Parser pipeline.

Runs the following stages in order:
  1. Document ingestion - reads complete Markdown specification files
  2. Markdown structure extraction - extracts structure from complete documents

This module exposes `run_pipeline` which returns a structured summary of the
execution. The input path is read from :mod:`shared.config.settings` when a
path is not explicitly provided.
"""
from __future__ import annotations

import json
import logging
import sys
import importlib
from pathlib import Path
from typing import Iterable

# Defer importing project-local modules until `run_pipeline` so this module can
# be imported in test runners or executed as a script from different CWDs.
settings = None

logger = logging.getLogger(__name__)

# Module-level hooks that tests can monkeypatch. When `None` the
# real implementations are imported lazily inside `run_pipeline`.
load_documents = None
extract_structure_from_documents = None


def _prepare_import_paths() -> Path:
    """Ensure the repository root and `2_Parsers` folder are on `sys.path`.

    Returns the repository base path (POC directory).
    """
    # Compute paths relative to this file's absolute location so this works
    # regardless of the current working directory.
    #   parents[0] = .../POC/2_Parsers/markdown_parser
    #   parents[1] = .../POC/2_Parsers          (needed for `import markdown_parser`)
    #   parents[2] = .../POC                    (needed for `import shared`)
    #   parents[3] = .../paddyMan               (project root; used as base for
    #                                            resolving relative config paths
    #                                            such as "POC/DataSource/...")
    script = Path(__file__).resolve()
    repo_root = script.parents[3]
    poc_root = script.parents[2]
    two_parsers = script.parents[1]

    # Insert `2_Parsers` first so `import markdown_parser` resolves, then
    # insert `POC/` so `import shared` resolves.
    sp = sys.path
    for p in (str(two_parsers), str(poc_root)):
        if p not in sp:
            sp.insert(0, p)

    return repo_root


def run_pipeline(source_dir: Path | str | None = None) -> dict:
    """Run the end-to-end Markdown Parser pipeline and return a summary.

    Args:
        source_dir: Optional source directory path. When omitted the value is
            read from :data:`shared.config.settings.markdown_spec_dir`.

    Returns:
        Summary dictionary with counts for documents, sections,
        headings, references, tables, and any errors encountered.
    """
    errors: list[str] = []

    # Ensure imports work when running as a script from other CWDs.
    base = _prepare_import_paths()

    # Resolve settings: prefer module-level `settings` when tests monkeypatch
    # it; otherwise import from `shared.config`.
    global settings
    if settings is None:
        try:
            cfg_mod = importlib.import_module("shared.config")
            settings = getattr(cfg_mod, "settings")
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Could not import shared.config.settings: %s", exc)

    if source_dir is None:
        if settings is None:
            raise RuntimeError("No source_dir supplied and shared.config.settings not available")
        source_dir = settings.markdown_spec_dir

    # Normalize source_dir to an absolute path. If the configured path is
    # relative (common when running from a subdirectory), interpret it
    # relative to the repository base (`base` returned by
    # `_prepare_import_paths`). This avoids surprises when running the
    # script from inside `POC/` or other folders.
    source_path = Path(source_dir)
    if not source_path.is_absolute():
        source_path = base / source_path
    source_dir = source_path

    # Resolve pipeline stage callables. Tests can monkeypatch these at the
    # module level (e.g., main_mod.load_documents) so prefer globals first.
    load_documents = globals().get("load_documents")
    extract_structure_from_documents = globals().get("extract_structure_from_documents")

    if load_documents is None:
        reader_mod = importlib.import_module("markdown_parser.reader")
        load_documents = getattr(reader_mod, "load_documents")

    try:
        documents = load_documents(source_dir)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Document ingestion failed: %s", exc)
        return {
            "documents_loaded": 0,
            "sections_extracted": 0,
            "headings_found": 0,
            "references_found": 0,
            "tables_found": 0,
            "errors": [f"ingestion: {exc}"],
        }

    docs_loaded = len(documents or [])

    if docs_loaded == 0:
        return {
            "documents_loaded": 0,
            "sections_extracted": 0,
            "headings_found": 0,
            "references_found": 0,
            "tables_found": 0,
            "errors": [],
        }

    # Structure extraction
    if extract_structure_from_documents is None:
        struct_mod = importlib.import_module("markdown_parser.structure")
        extract_structure_from_documents = getattr(struct_mod, "extract_structure_from_documents")

    try:
        structures = extract_structure_from_documents(documents)
    except Exception as exc:
        logger.exception("Structure extraction failed: %s", exc)
        structures = []
        errors.append(f"structure: {exc}")

    # Aggregate counts
    sections_count = sum(len(s.get("sections", [])) for s in structures)
    headings_count = sum(len(s.get("headings", [])) for s in structures)
    refs_count = sum(
        len(s.get("references", {}).get("inline", []))
        + len(s.get("references", {}).get("definitions", []))
        + len(s.get("references", {}).get("citations", []))
        for s in structures
    )
    tables_count = sum(len(s.get("tables", [])) for s in structures)

    summary = {
        "documents_loaded": docs_loaded,
        "sections_extracted": sections_count,
        "headings_found": headings_count,
        "references_found": refs_count,
        "tables_found": tables_count,
        "errors": errors,
    }

    # Print a concise machine-readable summary
    print(json.dumps(summary, indent=2))

    return summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the Markdown Parser pipeline")
    parser.add_argument("source_dir", nargs="?", help="Optional path to source documents")
    args = parser.parse_args()

    # Ensure import paths are set up first
    base = _prepare_import_paths()

    # Determine source directory (same logic as run_pipeline)
    source_path = Path(args.source_dir) if args.source_dir else None
    if source_path is None:
        if settings is None:
            from shared.config import settings as cfg_settings
            settings_obj = cfg_settings
        else:
            settings_obj = settings
        source_path = Path(settings_obj.markdown_spec_dir)
        if not source_path.is_absolute():
            source_path = base / source_path
    
    result = run_pipeline(source_path)
    
    # Write markdown parser output with section hierarchy
    from markdown_file_output import write_markdown_parser_output
    
    # Determine output directory (reuse settings_obj if already loaded)
    if 'settings_obj' not in locals():
        if settings is None:
            from shared.config import settings as cfg_settings
            settings_obj = cfg_settings
        else:
            settings_obj = settings
    
    parser_output_dir = Path(settings_obj.parser_output_dir)
    if not parser_output_dir.is_absolute():
        base = _prepare_import_paths()
        parser_output_dir = base / parser_output_dir
    
    markdown_output_dir = parser_output_dir / "markdown"
    
    # Write per-specification JSON files with section hierarchy
    write_markdown_parser_output(source_path, markdown_output_dir)
    logger.info("Markdown parser output written to %s", markdown_output_dir)
