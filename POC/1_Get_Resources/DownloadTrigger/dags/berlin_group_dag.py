"""Airflow DAG: download all Berlin Group documentation (idempotent)."""
from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import datetime, timedelta

from airflow.decorators import dag, task

from berlin_group.config import ACTIVE_SOURCES, DOWNLOAD_BASE_DIR
from berlin_group.downloader import download_file
from berlin_group.models import DownloadLink
from berlin_group.scraper import scrape_source
import shared.schedules as _schedules
from shared.dag_config import (
    BERLIN_GROUP_PDF_DAG_RETRIES,
    DAG_MAX_ACTIVE_RUNS,
    PDF_DOWNLOAD_TASK_RETRIES,
    PDF_DOWNLOAD_TASK_RETRY_SECONDS,
    dag_default_args,
)

_sched = _schedules.BERLIN_GROUP_PDF

logger = logging.getLogger(__name__)

@dag(
    dag_id="berlin_group_pdf_downloader",
    description="Download NextGenPSD2 and OpenFinance documentation from berlin-group.org.",
    schedule=_sched.effective_schedule,
    start_date=datetime(2024, 1, 1),
    catchup=_sched.catchup,
    default_args=dag_default_args(retries=BERLIN_GROUP_PDF_DAG_RETRIES),
    tags=["berlin-group", "documentation", "download"],
    max_active_runs=DAG_MAX_ACTIVE_RUNS,
    doc_md=__doc__,
)
def berlin_group_downloader() -> None:

    @task
    def discover_source(source_config: dict) -> list[dict]:
        """Scrape one source page and return serialisable link records."""
        links = scrape_source(
            source_config["url"],
            source_config["name"],
            title_field=source_config.get("title_field", "Document title and Version"),
            use_title_as_filename=source_config.get("use_title_as_filename", False),
            trailing_version=source_config.get("trailing_version", False),
            version_major=source_config.get("version_major"),
        )
        logger.info(
            "Discovered %d link(s) for %s", len(links), source_config["name"]
        )
        return [asdict(link) for link in links]

    @task
    def flatten_links(links_per_source: list[list[dict]]) -> list[dict]:
        """Merge per-source lists into a single flat list for downstream mapping."""
        flat = [link for group in links_per_source for link in group]
        logger.info("Total links to process: %d", len(flat))
        return flat

    @task(retries=PDF_DOWNLOAD_TASK_RETRIES, retry_delay=timedelta(seconds=PDF_DOWNLOAD_TASK_RETRY_SECONDS))
    def download_document(link_info: dict) -> dict:
        """Download one document; skip if the local file already exists."""
        link = DownloadLink(**link_info)
        result = download_file(link, base_dir=DOWNLOAD_BASE_DIR)
        logger.info(
            "[%s] %s/%s/%s",
            result.status,
            link.source_name,
            link.version,
            link.filename,
        )
        return {
            "url": link.url,
            "status": result.status,
            "local_path": result.local_path,
            "error": result.error,
        }

    @task(trigger_rule="all_done")
    def summarize_run(all_results: list[dict]) -> None:
        """Log a run summary: downloaded, skipped, and failed document counts."""
        from shared.idempotency import log_run_summary

        display = [
            {**r, "status": "downloaded" if r.get("status") == "success" else r.get("status")}
            for r in all_results
        ]
        log_run_summary(display, logger)

    @task
    def setup_dirs() -> None:
        """Create configured destination directories before any download runs."""
        from shared.dirs import ensure_destinations
        ensure_destinations()

    source_dicts = [asdict(s) for s in ACTIVE_SOURCES]
    dirs_ready = setup_dirs()
    discovered = discover_source.expand(source_config=source_dicts)
    dirs_ready >> discovered
    all_links = flatten_links(discovered)
    results = download_document.expand(link_info=all_links)
    summarize_run(results)


berlin_group_downloader()
