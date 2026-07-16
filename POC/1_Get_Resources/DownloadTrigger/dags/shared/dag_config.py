"""Airflow-specific DAG configuration.

Contains only settings that are specific to the Airflow runtime environment.

Project-wide configuration (HTTP, Git, directories, source lists, logging)
is owned by ``poc_shared.config.settings`` — import from there directly:

    from poc_shared.config import settings

    settings.http_request_timeout
    settings.berlin_group_download_dir
    settings.gitlab_token

Configuration reference:  POC/.env.example
"""
from __future__ import annotations

import os
from datetime import timedelta

# ── Airflow-specific filesystem paths ─────────────────────────────────────────

LOG_DIR: str = os.environ.get("LOG_DIR", "/opt/airflow/logs")
TMP_DIR: str = os.environ.get("TMP_DIR", "/tmp/airflow_downloads")

# ── Airflow DAG defaults ──────────────────────────────────────────────────────

DAG_OWNER: str = os.environ.get("DAG_OWNER", "adorsys-download-trigger")
DAG_RETRIES: int = int(os.environ.get("DAG_RETRIES", "1"))
DAG_RETRY_DELAY_MINUTES: int = int(os.environ.get("DAG_RETRY_DELAY_MINUTES", "5"))
DAG_MAX_ACTIVE_RUNS: int = int(os.environ.get("DAG_MAX_ACTIVE_RUNS", "1"))

BERLIN_GROUP_PDF_DAG_RETRIES: int = int(
    os.environ.get("BERLIN_GROUP_PDF_DAG_RETRIES", "2")
)
PDF_DOWNLOAD_TASK_RETRIES: int = int(os.environ.get("PDF_DOWNLOAD_TASK_RETRIES", "3"))
PDF_DOWNLOAD_TASK_RETRY_SECONDS: int = int(
    os.environ.get("PDF_DOWNLOAD_TASK_RETRY_SECONDS", "30")
)


def dag_default_args(**overrides: object) -> dict:
    """Return a default_args dict ready for any DAG definition.

    Keyword arguments override individual keys, e.g.::

        dag_default_args(retries=BERLIN_GROUP_PDF_DAG_RETRIES)
    """
    base: dict = {
        "owner": DAG_OWNER,
        "retries": DAG_RETRIES,
        "retry_delay": timedelta(minutes=DAG_RETRY_DELAY_MINUTES),
        "email_on_failure": False,
        "email_on_retry": False,
    }
    base.update(overrides)
    return base
