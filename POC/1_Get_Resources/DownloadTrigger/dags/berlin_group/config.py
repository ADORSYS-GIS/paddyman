"""Configuration for the Berlin Group PDF downloader.

Source URLs and metadata are loaded from the ``PDF_SOURCES`` environment
variable (JSON array).  No URLs are hardcoded here.
See .env.example for the expected format.
"""
from __future__ import annotations

from poc_shared.config import settings as _cfg
from shared.loaders import load_pdf_sources
from shared.models import SourceConfig  # re-exported for downstream imports

DOWNLOAD_BASE_DIR = _cfg.berlin_group_download_dir
DOWNLOAD_CHUNK_SIZE: int = _cfg.http_chunk_size
DOWNLOAD_TIMEOUT_SECONDS: int = _cfg.http_request_timeout
HTTP_RETRIES: int = _cfg.http_retries
RETRY_BACKOFF_FACTOR: float = _cfg.http_retry_backoff
RETRY_STATUS_CODES: frozenset[int] = _cfg.http_retry_status_codes
USER_AGENT: str = _cfg.http_user_agent
PDF_SOURCES_JSON: str = _cfg.pdf_sources_json
SCRAPER_POST_LOAD_WAIT_MS: int = _cfg.scraper_post_load_wait_ms
SCRAPER_TIMEOUT_MS: int = _cfg.scraper_timeout_ms

__all__ = [
    "DOWNLOAD_BASE_DIR",
    "DOWNLOAD_CHUNK_SIZE",
    "DOWNLOAD_TIMEOUT_SECONDS",
    "HTTP_RETRIES",
    "RETRY_BACKOFF_FACTOR",
    "RETRY_STATUS_CODES",
    "USER_AGENT",
    "SCRAPER_POST_LOAD_WAIT_MS",
    "SCRAPER_TIMEOUT_MS",
    "SourceConfig",
    "SOURCES",
    "ACTIVE_SOURCES",
]

SOURCES: list[SourceConfig] = load_pdf_sources(PDF_SOURCES_JSON)
ACTIVE_SOURCES: list[SourceConfig] = [s for s in SOURCES if s.enabled]
