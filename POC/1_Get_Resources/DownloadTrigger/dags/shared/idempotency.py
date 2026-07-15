"""Shared idempotency helpers used by all downloader workflows."""
from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CloneResult:
    """Outcome of a single repository clone attempt."""

    repo_name: str
    status: str  # "cloned" | "skipped"


def repo_exists(dest: Path) -> bool:
    """Return True when *dest* is an initialised git repository."""
    return dest.exists() and (dest / ".git").exists()


def log_run_summary(results: list[dict], logger: logging.Logger) -> None:
    """Log a count of each status value present in *results*.

    Expects each item to have a ``"status"`` key.  Any item whose status is
    ``"failed"`` is also listed by name (``"repo"`` or ``"url"`` key).
    """
    counts = Counter(r.get("status", "unknown") for r in results)
    parts = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
    logger.info("Run summary — %s", parts)

    failed = [
        r.get("repo") or r.get("url", "?")
        for r in results
        if r.get("status") == "failed"
    ]
    if failed:
        logger.warning("Failed items: %s", failed)
