"""Airflow DAG: clone Adorsys XS2A GitLab repositories (idempotent)."""
from __future__ import annotations

import logging
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from adorsys_clone.config import ACTIVE_REPOS as REPOS, ADORSYS_CODE_DIR, RepoConfig
import shared.schedules as _schedules
from shared.dag_config import (
    DAG_MAX_ACTIVE_RUNS,
    dag_default_args,
)

_sched = _schedules.ADORSYS

logger = logging.getLogger(__name__)


def _run_clone(repo_path: str, local_name: str) -> dict:
    """PythonOperator callable: clone a single Adorsys repository if not already present.

    Import is deferred so Airflow can parse the DAG file without requiring
    python-gitlab and gitpython at scheduler parse time.
    """
    from adorsys_clone.service import clone_or_update  # deferred import

    config = RepoConfig(path=repo_path, local_name=local_name)
    result = clone_or_update(config, ADORSYS_CODE_DIR)
    logger.info("Finished %s — %s", repo_path, result.status)
    return {"repo": local_name, "status": result.status}


def _summarize_run(task_ids: list[str], **context) -> None:  # type: ignore[override]
    """Collect per-repo XCom results and log a run summary."""
    from shared.idempotency import log_run_summary

    ti = context["ti"]
    results = []
    for tid in task_ids:
        val = ti.xcom_pull(task_ids=tid)
        results.append(val if val is not None else {"repo": tid, "status": "failed"})
    log_run_summary(results, logger)


with DAG(
    dag_id="adorsys_code_repo_downloader",
    description="Clone Adorsys XS2A GitLab repositories into DataSource/code_projects.",
    schedule=_sched.effective_schedule,
    start_date=datetime(2024, 1, 1),
    catchup=_sched.catchup,
    default_args=dag_default_args(),
    tags=["adorsys", "gitlab", "clone", "xs2a"],
    max_active_runs=DAG_MAX_ACTIVE_RUNS,
    doc_md=__doc__,
) as dag:

    def _setup_dirs() -> None:
        from shared.dirs import ensure_destinations
        ensure_destinations()

    start = PythonOperator(task_id="setup_dirs", python_callable=_setup_dirs)

    clone_task_ids: list[str] = []
    prev = start
    for _repo in REPOS:
        _tid = f"clone_{_repo.local_name.replace('-', '_')}"
        clone_task_ids.append(_tid)
        _clone_task = PythonOperator(
            task_id=_tid,
            python_callable=_run_clone,
            op_kwargs={"repo_path": _repo.path, "local_name": _repo.local_name},
        )
        prev >> _clone_task
        prev = _clone_task

    finish = PythonOperator(
        task_id="finish",
        python_callable=_summarize_run,
        op_kwargs={"task_ids": clone_task_ids},
        trigger_rule="all_done",
    )
    prev >> finish
