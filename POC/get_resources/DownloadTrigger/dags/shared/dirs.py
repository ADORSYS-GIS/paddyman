"""Shared directory setup utility.

Creates all configured destination directories before any download or
processing step runs.  All operations are idempotent — existing directories
are left untouched.
"""
from __future__ import annotations

import logging
from pathlib import Path

from poc_shared.config import settings as _cfg

ADORSYS_CODE_DIR = _cfg.adorsys_code_dir
BERLIN_GROUP_DOWNLOAD_DIR = _cfg.berlin_group_download_dir
YAML_SPEC_DIR = _cfg.yaml_spec_dir

logger = logging.getLogger(__name__)

_DESTINATIONS: tuple[Path, ...] = (
    BERLIN_GROUP_DOWNLOAD_DIR,
    YAML_SPEC_DIR,
    ADORSYS_CODE_DIR,
)


def ensure_destinations() -> None:
    """Create every configured destination directory if it does not exist.

    Safe to call multiple times — uses ``mkdir(parents=True, exist_ok=True)``
    so existing directories and their contents are never modified.
    """
    for directory in _DESTINATIONS:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug("Directory ready: %s", directory)
    logger.info(
        "Destination directories verified (%d paths).", len(_DESTINATIONS)
    )
