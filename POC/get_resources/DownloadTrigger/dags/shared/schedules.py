"""Centralised scheduling configuration for all download DAGs.

Override any value via environment variables; see README for the full list.
Switching schedules requires only a config/env-var change — no DAG code edits.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Preset cron expressions (each independently overridable via env var)
# ---------------------------------------------------------------------------

#: First day of every month at midnight.
MONTHLY: str = os.environ.get("SCHEDULE_MONTHLY", "0 0 1 * *")

#: Every Sunday at midnight.  Override ``SCHEDULE_WEEKLY`` to change the day/time.
WEEKLY: str = os.environ.get("SCHEDULE_WEEKLY", "0 0 * * 0")

#: Every day at midnight.  Override ``SCHEDULE_DAILY`` to change the time.
DAILY: str = os.environ.get("SCHEDULE_DAILY", "0 0 * * *")


# ---------------------------------------------------------------------------
# Per-DAG schedule config
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DagScheduleConfig:
    """Scheduling knobs for a single Airflow DAG.

    Attributes:
        schedule:  Cron expression or Airflow preset (``@daily``, etc.).
        enabled:   ``False`` → schedule becomes ``None`` (manual trigger only).
        catchup:   Whether Airflow should backfill missed intervals.
    """

    schedule: str
    enabled: bool = True
    catchup: bool = False

    @property
    def effective_schedule(self) -> str | None:
        """Cron string, or ``None`` when the DAG is disabled."""
        return self.schedule if self.enabled else None


def _bool_env(var: str, default: bool) -> bool:
    """Read a boolean from *var* with a typed *default* fallback."""
    raw = os.environ.get(var)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes"}


# -- Berlin Group PDF downloader ---------------------------------------------

BERLIN_GROUP_PDF: DagScheduleConfig = DagScheduleConfig(
    schedule=os.environ.get("BERLIN_GROUP_PDF_SCHEDULE", MONTHLY),
    enabled=_bool_env("BERLIN_GROUP_PDF_ENABLED", True),
    catchup=_bool_env("BERLIN_GROUP_PDF_CATCHUP", False),
)

# -- Berlin Group YAML repository cloner -------------------------------------

BERLIN_GROUP_YAML: DagScheduleConfig = DagScheduleConfig(
    schedule=os.environ.get("BERLIN_GROUP_YAML_SCHEDULE", MONTHLY),
    enabled=_bool_env("BERLIN_GROUP_YAML_ENABLED", True),
    catchup=_bool_env("BERLIN_GROUP_YAML_CATCHUP", False),
)

# -- Adorsys XS2A code repository cloner ------------------------------------

ADORSYS: DagScheduleConfig = DagScheduleConfig(
    schedule=os.environ.get("ADORSYS_SCHEDULE", MONTHLY),
    enabled=_bool_env("ADORSYS_ENABLED", True),
    catchup=_bool_env("ADORSYS_CATCHUP", False),
)
