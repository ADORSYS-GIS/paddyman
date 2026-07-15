"""
Batch converter: find every PDF under DownloadTrigger/downloads that has
not yet been fully processed and run the Docling pipeline:

  1. convert        — Docling PDF -> raw Markdown + metadata JSON
  2. postprocess    — clean/normalize the raw Markdown

Final cleaned Markdown files are written directly to the specification
directory (berlin_group_specification_md_files) without intermediate storage.

A PDF is considered fully processed when its cleaned Markdown file exists in
the specification directory. Re-running is safe and idempotent.

All PDFs are processed concurrently for maximum throughput. Worker count is
configurable via shared.config (docling.max_workers). A value of 0 uses
CPU count - 1.

Usage (from POC/1_Get_Resources/Docling/):
    source .venv/bin/activate
    python batch_convert.py

Options:
    --downloads  DIR     PDFs root            (env: DOCLING_DOWNLOADS_DIR)
    --spec-dir   DIR     cleaned MD output    (env: MARKDOWN_SPEC_DIR)
    --picture-mode MODE  none | local | api   (env: DOCLING_PICTURE_MODE)
    --max-workers INT    concurrent workers   (env: DOCLING_MAX_WORKERS)
"""
from __future__ import annotations

import argparse
import logging
import os
import pathlib
import re
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Literal

from dotenv import load_dotenv

from pipeline import (
    build_converter,
    convert_pdf,
    postprocess_pdf,
)

# Load shared configuration from the Get Resources root directory.
# Both DownloadTrigger and Docling share a single .env at POC/1_Get_Resources/.env.
_ENV_FILE = pathlib.Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_FILE)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProcessingResult:
    """Result of processing a single PDF."""

    pdf_name: str
    slug: str
    status: Literal["success", "skipped", "failed"]
    error_message: str | None = None
    elapsed_seconds: float | None = None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_HERE = pathlib.Path(__file__).parent.resolve()

_parser = argparse.ArgumentParser(
    description="Batch-convert Berlin Group PDFs through the full Docling pipeline."
)
_parser.add_argument(
    "--downloads",
    default=os.environ.get("DOCLING_DOWNLOADS_DIR", str(_HERE / "../DownloadTrigger/downloads")),
    help="Root directory containing downloaded PDFs",
)
_parser.add_argument(
    "--spec-dir",
    default=os.environ.get(
        "MARKDOWN_SPEC_DIR",
        str(_HERE / "../../DataSource/berlin_group_specification_md_files")
    ),
    help="Output directory for cleaned specification Markdown files",
)
_parser.add_argument(
    "--picture-mode",
    choices=["none", "local", "api"],
    default=os.environ.get("DOCLING_PICTURE_MODE", "none"),
    dest="picture_mode",
    help="Picture description mode: none | local | api",
)
_parser.add_argument(
    "--max-workers",
    type=int,
    default=int(os.environ.get("DOCLING_MAX_WORKERS", "0")),
    dest="max_workers",
    help="Number of concurrent workers (0 = CPU count - 1)",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_slug(pdf_path: pathlib.Path) -> str:
    """Derive a filesystem-safe slug from a PDF filename (no extension)."""
    return re.sub(r"[^a-z0-9]+", "_", pdf_path.stem.lower()).strip("_")


def is_processed(slug: str, spec_dir: pathlib.Path) -> bool:
    """Return True if the cleaned Markdown file exists in the spec directory.

    Checks for the existence of ``<slug>_clean.md`` in the specification directory.
    """
    clean_md_file = spec_dir / f"{slug}_clean.md"
    return clean_md_file.exists()


def find_pdfs(downloads_dir: pathlib.Path) -> list[pathlib.Path]:
    """Find all PDF files in the downloads directory."""
    return sorted(downloads_dir.rglob("*.pdf"))


def get_worker_count(max_workers: int) -> int:
    """Compute actual worker count from configuration.

    Args:
        max_workers: Configured value (0 = auto-detect).

    Returns:
        Number of concurrent workers to use (minimum 1).
    """
    if max_workers > 0:
        return max_workers
    
    import multiprocessing
    cpu_count = multiprocessing.cpu_count()
    return max(1, cpu_count - 1)


def process_single_pdf(
    pdf_path: pathlib.Path,
    spec_dir: pathlib.Path,
    picture_mode: str,
) -> ProcessingResult:
    """Process a single PDF through the Docling pipeline.

    Args:
        pdf_path: Path to PDF file.
        spec_dir: Target specification directory.
        picture_mode: Picture description mode (none | local | api).

    Returns:
        ProcessingResult indicating success, skip, or failure.
    """
    slug = make_slug(pdf_path)
    pdf_name = pdf_path.name
    start_time = time.time()

    try:
        # Check if already processed
        if is_processed(slug, spec_dir):
            return ProcessingResult(
                pdf_name=pdf_name,
                slug=slug,
                status="skipped",
                elapsed_seconds=time.time() - start_time,
            )

        # Build converter for this PDF
        converter = build_converter(picture_mode)

        # Step 1: Convert PDF to Markdown (returns markdown string)
        raw_markdown = convert_pdf(converter, pdf_path, slug, spec_dir, picture_mode)

        # Step 2: Postprocess (clean) the Markdown and write final file
        postprocess_pdf(raw_markdown, slug, spec_dir)

        elapsed = time.time() - start_time
        return ProcessingResult(
            pdf_name=pdf_name,
            slug=slug,
            status="success",
            elapsed_seconds=elapsed,
        )

    except Exception as exc:
        elapsed = time.time() - start_time
        error_msg = str(exc)
        logger.error("Failed to process %s: %s", pdf_name, error_msg)
        logger.debug("Stack trace:\n%s", traceback.format_exc())
        
        return ProcessingResult(
            pdf_name=pdf_name,
            slug=slug,
            status="failed",
            error_message=error_msg,
            elapsed_seconds=elapsed,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    args = _parser.parse_args()
    
    downloads_dir = pathlib.Path(args.downloads).resolve()
    spec_dir = pathlib.Path(args.spec_dir).resolve()
    picture_mode: str = args.picture_mode
    max_workers = args.max_workers

    if not downloads_dir.exists():
        logger.error("Downloads directory not found: %s", downloads_dir)
        sys.exit(1)

    spec_dir.mkdir(parents=True, exist_ok=True)

    pdfs = find_pdfs(downloads_dir)
    if not pdfs:
        logger.warning("No PDFs found under %s", downloads_dir)
        return

    total_pdfs = len(pdfs)
    worker_count = get_worker_count(max_workers)
    
    logger.info("Found %d PDF(s) under %s", total_pdfs, downloads_dir)
    logger.info("Using %d concurrent workers", worker_count)
    logger.info("")

    start_time = time.time()
    results: list[ProcessingResult] = []
    completed = 0

    # Process PDFs concurrently using threads
    # ThreadPoolExecutor avoids serialization issues with Docling's PDF backends
    # while still benefiting from concurrency (OCR/image ops release GIL)
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        # Submit all tasks
        futures = {
            executor.submit(
                process_single_pdf,
                pdf_path,
                spec_dir,
                picture_mode,
            ): pdf_path
            for pdf_path in pdfs
        }

        # Process results as they complete
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1

            # Log result
            _log_processing_result(result, completed, total_pdfs)

    # Generate summary
    _print_summary(results, total_pdfs, time.time() - start_time)

    # Exit with error code if any PDFs failed
    failed_results = [r for r in results if r.status == "failed"]
    if failed_results:
        _print_failed_pdfs(failed_results)
        sys.exit(1)


def _log_processing_result(result: ProcessingResult, completed: int, total: int) -> None:
    """Log the result of processing a single PDF.

    Args:
        result: Processing result.
        completed: Number of PDFs completed so far.
        total: Total number of PDFs.
    """
    elapsed_str = f"{result.elapsed_seconds:.1f}s" if result.elapsed_seconds else "N/A"
    
    if result.status == "success":
        logger.info(
            "[%d/%d] ✓ %s (%s)",
            completed,
            total,
            result.pdf_name,
            elapsed_str,
        )
    elif result.status == "skipped":
        logger.info(
            "[%d/%d] ⊘ %s (already processed)",
            completed,
            total,
            result.pdf_name,
        )
    else:  # failed
        logger.error(
            "[%d/%d] ✗ %s (%s): %s",
            completed,
            total,
            result.pdf_name,
            elapsed_str,
            result.error_message or "unknown error",
        )


def _print_summary(results: list[ProcessingResult], total: int, elapsed: float) -> None:
    """Print execution summary.

    Args:
        results: All processing results.
        total: Total number of PDFs.
        elapsed: Total elapsed seconds.
    """
    successful = sum(1 for r in results if r.status == "success")
    skipped = sum(1 for r in results if r.status == "skipped")
    failed = sum(1 for r in results if r.status == "failed")

    logger.info("")
    logger.info("=" * 70)
    logger.info("Summary:")
    logger.info("  Total PDFs:         %d", total)
    logger.info("  Successful:         %d", successful)
    logger.info("  Skipped:            %d", skipped)
    logger.info("  Failed:             %d", failed)
    logger.info("  Total time:         %.1fs", elapsed)
    
    if successful > 0:
        avg_time = sum(
            r.elapsed_seconds for r in results 
            if r.status == "success" and r.elapsed_seconds
        ) / successful
        logger.info("  Avg time per PDF:   %.1fs", avg_time)
    
    logger.info("=" * 70)


def _print_failed_pdfs(failed_results: list[ProcessingResult]) -> None:
    """Print list of failed PDFs.

    Args:
        failed_results: List of failed processing results.
    """
    logger.info("")
    logger.info("Failed PDFs:")
    for result in failed_results:
        logger.info("  • %s: %s", result.pdf_name, result.error_message)


if __name__ == "__main__":
    main()
