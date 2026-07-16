"""Configuration for the GitLab YAML repository cloning service.

Repository paths are loaded from the ``YAML_REPOS`` environment variable
(JSON array).  No repository paths are hardcoded here.
See .env.example for the expected format.
"""
from __future__ import annotations

from poc_shared.config import settings as _cfg
from shared.loaders import load_repos
from shared.models import RepoConfig  # re-exported for downstream imports

GITLAB_BASE_URL: str = _cfg.gitlab_base_url
GITLAB_TOKEN: str | None = _cfg.gitlab_token
YAML_REPOS_JSON: str = _cfg.yaml_repos_json
YAML_SPEC_DIR = _cfg.yaml_spec_dir

__all__ = [
    "GITLAB_BASE_URL",
    "GITLAB_TOKEN",
    "YAML_SPEC_DIR",
    "RepoConfig",
    "REPOS",
    "ACTIVE_REPOS",
]

REPOS: list[RepoConfig] = load_repos(YAML_REPOS_JSON, "YAML_REPOS")
ACTIVE_REPOS: list[RepoConfig] = [r for r in REPOS if r.enabled]
