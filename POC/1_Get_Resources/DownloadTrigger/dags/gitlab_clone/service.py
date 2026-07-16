"""GitLab repository clone operations (idempotent — skip existing repos)."""
from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import gitlab
from dulwich import porcelain
from dulwich.errors import GitProtocolError, NotGitRepository
from gitlab.exceptions import GitlabAuthenticationError, GitlabError

from gitlab_clone.config import GITLAB_BASE_URL, GITLAB_TOKEN, RepoConfig
from shared.idempotency import CloneResult, repo_exists

logger = logging.getLogger(__name__)

# dulwich emits noisy progress to stderr by default; silence it
_DEVNULL = open("/dev/null", "wb")  # noqa: WPS515


# ── GitLab client ──────────────────────────────────────────────────────────────


def _build_gitlab_client() -> gitlab.Gitlab:
    """Return an authenticated (or anonymous) GitLab client.

    If the configured token is present but rejected by the server (e.g. it is
    expired or belongs to a different GitLab instance), authentication is
    silently downgraded to anonymous access.  Public repositories such as
    the-berlin-group/nextgenpsd2 are still cloneable without a token.
    """
    client = gitlab.Gitlab(GITLAB_BASE_URL, private_token=GITLAB_TOKEN)
    if GITLAB_TOKEN:
        try:
            client.auth()
        except GitlabAuthenticationError:
            logger.warning(
                "GitLab token rejected (%s) — falling back to anonymous access. "
                "Private repositories will fail at clone time.",
                GITLAB_BASE_URL,
            )
            client = gitlab.Gitlab(GITLAB_BASE_URL)
    return client


def _default_branch(client: gitlab.Gitlab, repo_path: str) -> str:
    """Return the default branch name for *repo_path*."""
    project = client.projects.get(repo_path)
    return str(project.default_branch)


# ── Clone URL builder ──────────────────────────────────────────────────────────


def _clone_url(repo_path: str) -> str:
    """Build a clone URL, embedding the PAT when one is configured."""
    parsed = urlparse(GITLAB_BASE_URL)
    netloc = (
        f"oauth2:{GITLAB_TOKEN}@{parsed.hostname}"
        if GITLAB_TOKEN
        else parsed.hostname or ""
    )
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return urlunparse((parsed.scheme, netloc, f"/{repo_path}.git", "", "", ""))


# ── Git operation ──────────────────────────────────────────────────────────────


def _clone(url: str, dest: Path) -> None:
    """Clone *url* into *dest*, creating parent directories as needed."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    porcelain.clone(url, str(dest), errstream=_DEVNULL)
    logger.info("Cloned %s → %s", url.split("@")[-1], dest)


# ── Public entry point ─────────────────────────────────────────────────────────


def clone_or_update(repo_config: RepoConfig, dest_dir: Path) -> CloneResult:
    """Clone *repo_config* into *dest_dir*, skipping if it already exists.

    Returns a :class:`CloneResult` with status ``"skipped"`` when the
    repository is already present locally — no network calls are made in
    that case.  Raises on unrecoverable errors so the caller can mark the
    Airflow task as failed and trigger retries.
    """
    dest = dest_dir / repo_config.local_name

    if repo_exists(dest):
        logger.info(
            "Skipping YAML repository %s: already exists.", repo_config.local_name
        )
        return CloneResult(repo_name=repo_config.local_name, status="skipped")

    url = _clone_url(repo_config.path)

    try:
        client = _build_gitlab_client()
        _default_branch(client, repo_config.path)  # validates connectivity / auth
    except GitlabError as exc:
        logger.error("GitLab API error for %s: %s", repo_config.path, exc)
        raise

    try:
        _clone(url, dest)
        return CloneResult(repo_name=repo_config.local_name, status="cloned")
    except (GitProtocolError, NotGitRepository, OSError) as exc:
        logger.error("Git error for %s: %s", repo_config.path, exc)
        raise


