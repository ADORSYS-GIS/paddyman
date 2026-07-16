"""Adorsys GitLab clone operations (idempotent — skip existing repos).

Uses gitpython (system git binary) to handle large repositories reliably.
Shares idempotency utilities with gitlab_clone.service.
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import git as gitpython
import gitlab
from gitlab.exceptions import GitlabError

from adorsys_clone.config import ADORSYS_BASE_URL, ADORSYS_TOKEN, RepoConfig
from shared.idempotency import CloneResult, repo_exists

logger = logging.getLogger(__name__)


# ── Adorsys GitLab client ──────────────────────────────────────────────────────


def _build_adorsys_client() -> gitlab.Gitlab:
    """Return an authenticated GitLab client for the Adorsys instance.

    Raises :class:`EnvironmentError` with a clear message when the token is absent.
    """
    if not ADORSYS_TOKEN:
        raise EnvironmentError(
            "ADORSYS_GITLAB_TOKEN is not set. "
            "Add it to POC/.env and ensure "
            "it is exported into the Airflow environment."
        )
    client = gitlab.Gitlab(ADORSYS_BASE_URL, private_token=ADORSYS_TOKEN)
    client.auth()
    return client


# ── Clone URL builder ──────────────────────────────────────────────────────────


def _adorsys_clone_url(repo_path: str) -> str:
    """Build an authenticated HTTPS clone URL for *repo_path* on the Adorsys GitLab."""
    parsed = urlparse(ADORSYS_BASE_URL)
    netloc = (
        f"oauth2:{ADORSYS_TOKEN}@{parsed.hostname}"
        if ADORSYS_TOKEN
        else parsed.hostname or ""
    )
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return urlunparse((parsed.scheme, netloc, f"/{repo_path}.git", "", "", ""))


# ── Git operation (gitpython — delegates to system git binary) ─────────────────

# Increase the HTTP send/receive buffer to handle large repositories reliably.
_GIT_OPTIONS: list[str] = ["-c", "http.postBuffer=524288000"]
# Abort if transfer drops below 1 KB/s for more than 5 minutes.
_GIT_ENV: dict[str, str] = {
    "GIT_HTTP_LOW_SPEED_LIMIT": "1000",
    "GIT_HTTP_LOW_SPEED_TIME": "300",
}
_CLONE_ATTEMPTS: int = 3


def _clone(url: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    last_exc: Exception | None = None
    for attempt in range(1, _CLONE_ATTEMPTS + 1):
        try:
            gitpython.Repo.clone_from(
                url,
                str(dest),
                multi_options=_GIT_OPTIONS,
                env=_GIT_ENV,
                allow_unsafe_options=True,
            )
            logger.info("Cloned %s → %s", url.split("@")[-1], dest)
            return
        except (gitpython.GitCommandError, OSError) as exc:
            last_exc = exc
            logger.warning(
                "Clone attempt %d/%d failed for %s: %s",
                attempt,
                _CLONE_ATTEMPTS,
                url.split("@")[-1],
                exc,
            )
            if dest.exists():
                shutil.rmtree(dest, ignore_errors=True)
                dest.mkdir(parents=True, exist_ok=True)
    raise last_exc  # type: ignore[misc]


# ── Public entry point ─────────────────────────────────────────────────────────


def clone_or_update(repo_config: RepoConfig, dest_dir: Path) -> CloneResult:
    """Clone *repo_config* into *dest_dir*, skipping if it already exists.

    Returns a :class:`CloneResult` with status ``"skipped"`` when the
    repository is already present locally — no network calls are made.
    Raises on unrecoverable errors.
    """
    dest = dest_dir / repo_config.local_name

    if repo_exists(dest):
        logger.info(
            "Skipping Adorsys repository %s: already exists.", repo_config.local_name
        )
        return CloneResult(repo_name=repo_config.local_name, status="skipped")

    url = _adorsys_clone_url(repo_config.path)

    try:
        client = _build_adorsys_client()
        project = client.projects.get(repo_config.path)
        logger.info(
            "Resolved %s (default branch: %s)",
            repo_config.path,
            project.default_branch,
        )
    except GitlabError as exc:
        logger.error("GitLab API error for %s: %s", repo_config.path, exc)
        raise

    try:
        _clone(url, dest)
        return CloneResult(repo_name=repo_config.local_name, status="cloned")
    except (gitpython.GitCommandError, gitpython.InvalidGitRepositoryError, OSError) as exc:
        logger.error("Git error for %s: %s", repo_config.path, exc)
        raise

