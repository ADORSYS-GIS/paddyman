"""Unit tests for the Adorsys GitLab repository cloning service."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import git as gitpython
from gitlab.exceptions import GitlabAuthenticationError

from adorsys_clone.config import ADORSYS_BASE_URL, RepoConfig
from adorsys_clone.service import (
    _adorsys_clone_url,
    _build_adorsys_client,
    _clone,
    clone_or_update,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def repo_config() -> RepoConfig:
    return RepoConfig(path="adorsys/xs2a/aspsp-xs2a", local_name="aspsp-xs2a")


@pytest.fixture
def dest_dir(tmp_path: Path) -> Path:
    return tmp_path / "code_projects"


# ── _adorsys_clone_url ────────────────────────────────────────────────────────


def test_clone_url_contains_token() -> None:
    with patch("adorsys_clone.service.ADORSYS_TOKEN", "secret"):
        url = _adorsys_clone_url("adorsys/xs2a/aspsp-xs2a")
    assert "oauth2:secret@" in url
    assert url.endswith("/adorsys/xs2a/aspsp-xs2a.git")


def test_clone_url_no_token_omits_credentials() -> None:
    with patch("adorsys_clone.service.ADORSYS_TOKEN", None):
        url = _adorsys_clone_url("adorsys/xs2a/ledgers")
    assert "oauth2" not in url
    assert url.endswith("/adorsys/xs2a/ledgers.git")


def test_clone_url_uses_adorsys_base() -> None:
    with patch("adorsys_clone.service.ADORSYS_TOKEN", "t"):
        url = _adorsys_clone_url("adorsys/xs2a/aspsp-xs2a")
    assert "git.adorsys.de" in url


# ── _build_adorsys_client ─────────────────────────────────────────────────────


def test_build_client_raises_when_token_missing() -> None:
    with (
        patch("adorsys_clone.service.ADORSYS_TOKEN", None),
        pytest.raises(EnvironmentError, match="ADORSYS_GITLAB_TOKEN"),
    ):
        _build_adorsys_client()


def test_build_client_authenticates_with_token() -> None:
    with (
        patch("adorsys_clone.service.ADORSYS_TOKEN", "tok"),
        patch("adorsys_clone.service.gitlab.Gitlab") as mock_gl,
    ):
        mock_instance = MagicMock()
        mock_gl.return_value = mock_instance
        _build_adorsys_client()
    mock_gl.assert_called_once_with(ADORSYS_BASE_URL, private_token="tok")
    mock_instance.auth.assert_called_once()


# ── _clone / _update ──────────────────────────────────────────────────────────


def test_clone_creates_dest_and_calls_clone_from(tmp_path: Path) -> None:
    dest = tmp_path / "repo"
    with patch("adorsys_clone.service.gitpython.Repo.clone_from") as mock_cf:
        _clone("https://git.adorsys.de/org/repo.git", dest)
    mock_cf.assert_called_once_with("https://git.adorsys.de/org/repo.git", str(dest))
    assert dest.exists()


# ── clone_or_update ───────────────────────────────────────────────────────────


def test_clones_when_dest_absent(repo_config: RepoConfig, dest_dir: Path) -> None:
    with (
        patch("adorsys_clone.service._build_adorsys_client"),
        patch("adorsys_clone.service.ADORSYS_TOKEN", "tok"),
        patch("adorsys_clone.service._clone") as mock_clone,
    ):
        result = clone_or_update(repo_config, dest_dir)
    mock_clone.assert_called_once()
    assert result.status == "cloned"


def test_skips_when_dot_git_present(repo_config: RepoConfig, dest_dir: Path) -> None:
    """Existing repositories must be skipped — no network or git calls."""
    repo_dest = dest_dir / repo_config.local_name
    (repo_dest / ".git").mkdir(parents=True)
    with (
        patch("adorsys_clone.service._build_adorsys_client") as mock_client,
        patch("adorsys_clone.service._clone") as mock_clone,
    ):
        result = clone_or_update(repo_config, dest_dir)
    mock_client.assert_not_called()
    mock_clone.assert_not_called()
    assert result.status == "skipped"


def test_gitlab_error_propagates(repo_config: RepoConfig, dest_dir: Path) -> None:
    with (
        patch(
            "adorsys_clone.service._build_adorsys_client",
            side_effect=GitlabAuthenticationError("bad token"),
        ),
        pytest.raises(GitlabAuthenticationError),
    ):
        clone_or_update(repo_config, dest_dir)


def test_git_command_error_propagates(repo_config: RepoConfig, dest_dir: Path) -> None:
    with (
        patch("adorsys_clone.service._build_adorsys_client"),
        patch("adorsys_clone.service.ADORSYS_TOKEN", "tok"),
        patch(
            "adorsys_clone.service._clone",
            side_effect=gitpython.GitCommandError("clone", 128),
        ),
        pytest.raises(gitpython.GitCommandError),
    ):
        clone_or_update(repo_config, dest_dir)


def test_missing_token_raises_environment_error(
    repo_config: RepoConfig, dest_dir: Path
) -> None:
    with (
        patch("adorsys_clone.service.ADORSYS_TOKEN", None),
        pytest.raises(EnvironmentError, match="ADORSYS_GITLAB_TOKEN"),
    ):
        clone_or_update(repo_config, dest_dir)

