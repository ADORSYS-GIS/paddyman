"""Entity Extraction pipeline entry point — Phase 4.

Runs all extractor stages end-to-end:

    1. Load normalized JSON from the parser pipeline
  2. spaCy rule-based extraction + version-tag injection
  3. GLM structured extraction
  4. Triple generation
    5. Validation and summary

Usage (from POC/3_Extractors/)::

    python main.py

Or from the POC root::

    python -m 3_Extractors.main

All configuration is read through ``shared.config.settings``.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure POC/ and extractor sub-packages are importable from any CWD.
_here = Path(__file__).resolve().parent        # POC/3_Extractors/
_poc_root = _here.parent                       # POC/
_spacy_root = str(_here / "spacy")
_llm_root = str(_here / "llm")
_embed_root = str(_here / "embeddings")

# When run as `python 3_Extractors/main.py`, Python inserts the script
# directory (POC/3_Extractors/) at sys.path[0].  Remove it to prevent the
# local `spacy/` sub-package from shadowing the installed `spacy` library,
# then re-add it at the *end* so loader.py / extractor_pipeline.py are still
# importable but site-packages always wins for third-party names.
_here_str = str(_here)
if _here_str in sys.path:
    sys.path.remove(_here_str)

# Add POC/, spacy/, and llm/ roots at the front.
# _embed_root is intentionally NOT added globally: it shares `client/` and
# `services/` top-level names with llm/, causing import collisions.  The
# `embeddings` package is accessed as `embeddings.xxx` via _here_str below.
for _p in (str(_poc_root), _spacy_root, _llm_root):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Append extractors root last so `loader`, `extractor_pipeline`, and the
# `embeddings` sub-package (via `embeddings.xxx` imports) are all found
# without shadowing any installed packages.
if _here_str not in sys.path:
    sys.path.append(_here_str)

from shared.config import settings
from loader import load_all_records
from extractor_pipeline import ExtractionPipeline, PipelineSummary
from output_writer import open_writer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Component builders — isolate provider wiring from orchestration
# ---------------------------------------------------------------------------

def _build_spacy_pipeline():
    from pipeline.pipeline import SpacyExtractionPipeline
    return SpacyExtractionPipeline.build()


def _build_triple_service():
    from client.factory import create_client as create_llm_client
    from services.triple_service import TripleService
    return TripleService(client=create_llm_client())


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def _configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format=settings.log_format,
        stream=sys.stdout,
    )


def _print_summary(summary: PipelineSummary) -> None:
    separator = "=" * 60
    logger.info(separator)
    logger.info("Entity Extraction Pipeline — Summary")
    logger.info(separator)
    logger.info("  Records processed   : %d", summary.records_processed)
    logger.info("  spaCy entities      : %d", summary.spacy_entities)
    logger.info("  GLM entities        : %d", summary.llm_entities)
    logger.info("  Relationships       : %d", summary.relationships)
    logger.info("  Triples             : %d", summary.triples)
    logger.info("  Entity embeddings   : %d", summary.entity_embeddings)
    logger.info("  Chunk embeddings    : %d", summary.chunk_embeddings)
    logger.info("  Failures            : %d", len(summary.failures))
    if summary.failures:
        for failure in summary.failures:
            logger.warning("  [FAIL] %s", failure)
    logger.info(separator)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run() -> PipelineSummary:
    """Execute the complete extraction pipeline.

    Returns:
        :class:`PipelineSummary` with aggregated extraction counts.
    """
    logger.info("Phase 4 — Entity Extraction pipeline starting")

    # Stage 1: load normalized parser output
    records = load_all_records()
    if not records:
        logger.warning("No normalized parser records found — run the parser pipeline first")

    limit = settings.extraction_max_records
    if limit > 0 and len(records) > limit:
        logger.info("EXTRACTION_MAX_RECORDS=%d — capping %d records to %d", limit, len(records), limit)
        records = records[:limit]

    # Initialise extraction providers (fail fast on misconfiguration)
    spacy_pipeline = _build_spacy_pipeline()
    triple_service = _build_triple_service()

    # Stages 2–5: extraction pipeline
    writer = open_writer()
    pipeline = ExtractionPipeline(
        spacy_pipeline=spacy_pipeline,
        triple_service=triple_service,
        writer=writer,
    )
    try:
        summary = pipeline.run(records)
    finally:
        if writer is not None:
            writer.close()
    _print_summary(summary)
    return summary


if __name__ == "__main__":
    _configure_logging()
    run()
