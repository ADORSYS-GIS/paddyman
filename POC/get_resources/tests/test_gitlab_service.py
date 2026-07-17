"""Unit tests for the GitLab repository cloning service."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from dulwich.errors import GitProtocolError
from gitlab.exceptions import GitlabAuthenticationError

from gitlab_clone.config import RepoConfig
from gitlab_clone.service import (
    _clone,
    _clone_url,
    _default_branch,
    clone_or_update,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def repo_config() -> RepoConfig:
    return RepoConfig(path="the-berlin-group/nextgenpsd2", local_name="nextgenpsd2")


@pytest.fixture
def dest_dir(tmp_path: Path) -> Path:
    return tmp_path / "yaml_spec"


# ── _clone_url ─────────────────────────────────────────────────────────────────


def test_clone_url_anonymous() -> None:
    with patch("gitlab_clone.service.GITLAB_TOKEN", None):
        url = _clone_url("the-berlin-group/nextgenpsd2")
    assert "oauth2" not in url
    assert url.endswith("/the-berlin-group/nextgenpsd2.git")


def test_clone_url_with_token() -> None:
    with patch("gitlab_clone.service.GITLAB_TOKEN", "mytoken"):
        url = _clone_url("the-berlin-group/nextgenpsd2")
    assert "oauth2:mytoken@" in url
    assert url.endswith("/the-berlin-group/nextgenpsd2.git")


# ── _default_branch ────────────────────────────────────────────────────────────


def test_default_branch_returned() -> None:
    mock_client = MagicMock()
    mock_client.projects.get.return_value.default_branch = "main"
    branch = _default_branch(mock_client, "the-berlin-group/nextgenpsd2")
    assert branch == "main"
    mock_client.projects.get.assert_called_once_with("the-berlin-group/nextgenpsd2")


# ── _clone ─────────────────────────────────────────────────────────────────────


def test_clone_creates_dest_parent(tmp_path: Path) -> None:
    dest = tmp_path / "deep" / "nested" / "repo"
    with patch("gitlab_clone.service.porcelain.clone") as mock_clone:
        _clone("https://gitlab.com/org/repo.git", dest)
    mock_clone.assert_called_once()
    assert dest.parent.exists()


# ── clone_or_update ────────────────────────────────────────────────────────────


def test_clones_when_dest_absent(
    repo_config: RepoConfig, dest_dir: Path
) -> None:
    with (
        patch("gitlab_clone.service._build_gitlab_client"),
        patch("gitlab_clone.service._default_branch", return_value="main"),
        patch("gitlab_clone.service._clone") as mock_clone,
    ):
        result = clone_or_update(repo_config, dest_dir)
    mock_clone.assert_called_once()
    assert result.status == "cloned"


def test_skips_when_dot_git_present(
    repo_config: RepoConfig, dest_dir: Path
) -> None:
    """Existing repositories must be skipped — no network calls."""
    repo_dest = dest_dir / repo_config.local_name
    (repo_dest / ".git").mkdir(parents=True)

    with (
        patch("gitlab_clone.service._build_gitlab_client") as mock_client,
        patch("gitlab_clone.service._clone") as mock_clone,
    ):
        result = clone_or_update(repo_config, dest_dir)

    mock_client.assert_not_called()
    mock_clone.assert_not_called()
    assert result.status == "skipped"


def test_gitlab_api_error_propagates(
    repo_config: RepoConfig, dest_dir: Path
) -> None:
    with (
        patch(
            "gitlab_clone.service._build_gitlab_client",
            side_effect=GitlabAuthenticationError("bad token"),
        ),
        pytest.raises(GitlabAuthenticationError),
    ):
        clone_or_update(repo_config, dest_dir)


def test_git_error_propagates(
    repo_config: RepoConfig, dest_dir: Path
) -> None:
    with (
        patch("gitlab_clone.service._build_gitlab_client"),
        patch("gitlab_clone.service._default_branch", return_value="main"),
        patch(
            "gitlab_clone.service._clone",
            side_effect=GitProtocolError("connection refused"),
        ),
        pytest.raises(GitProtocolError),
    ):
        clone_or_update(repo_config, dest_dir)


