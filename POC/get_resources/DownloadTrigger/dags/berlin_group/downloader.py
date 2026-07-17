"""HTTP file downloader with idempotency and retry support."""
from __future__ import annotations

import logging
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import (
    DOWNLOAD_BASE_DIR,
    DOWNLOAD_CHUNK_SIZE,
    DOWNLOAD_TIMEOUT_SECONDS,
    HTTP_RETRIES,
    RETRY_BACKOFF_FACTOR,
    RETRY_STATUS_CODES,
    USER_AGENT,
)
from .models import DownloadLink, DownloadResult

logger = logging.getLogger(__name__)


# ── Session factory ────────────────────────────────────────────────────────────


def build_session() -> requests.Session:
    """Create a requests Session with retry logic and a shared User-Agent."""
    session = requests.Session()
    retry = Retry(
        total=HTTP_RETRIES,
        backoff_factor=RETRY_BACKOFF_FACTOR,
        status_forcelist=RETRY_STATUS_CODES,
        allowed_methods={"GET"},
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers["User-Agent"] = USER_AGENT
    return session


# ── Download ───────────────────────────────────────────────────────────────────


def _stream_to_file(response: requests.Response, target: Path) -> None:
    """Write a streamed response to *target*, creating parent dirs as needed."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as fh:
        for chunk in response.iter_content(DOWNLOAD_CHUNK_SIZE):
            if chunk:
                fh.write(chunk)


def download_file(
    link: DownloadLink,
    base_dir: Path = DOWNLOAD_BASE_DIR,
    session: requests.Session | None = None,
) -> DownloadResult:
    """Download *link* into *base_dir*, skipping if the file already exists."""
    target = link.target_path(base_dir)

    if target.exists():
        logger.info("Skip (exists): %s", target)
        return DownloadResult(link=link, success=True, skipped=True, local_path=str(target))

    owned = session is None
    if owned:
        session = build_session()

    try:
        logger.info("GET %s → %s", link.url, target)
        response = session.get(
            link.url, stream=True, timeout=DOWNLOAD_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        _stream_to_file(response, target)
        size = target.stat().st_size
        logger.info("Saved %s (%d bytes)", target, size)
        return DownloadResult(link=link, success=True, local_path=str(target))

    except Exception as exc:
        logger.error("Failed %s: %s", link.url, exc)
        target.unlink(missing_ok=True)  # remove partial file
        return DownloadResult(link=link, success=False, error=str(exc))

    finally:
        if owned:
            session.close()
