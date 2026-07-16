"""Configuration for the Adorsys XS2A code repository cloning service.

Repository paths are loaded from the ``CODE_REPOS`` environment variable
(JSON array).  No repository paths are hardcoded here.
See .env.example for the expected format.
"""
from __future__ import annotations

from poc_shared.config import settings as _cfg
from shared.loaders import load_repos
from shared.models import RepoConfig  # re-exported for downstream imports

ADORSYS_BASE_URL: str = _cfg.adorsys_base_url
ADORSYS_CODE_DIR = _cfg.adorsys_code_dir
ADORSYS_TOKEN: str | None = _cfg.adorsys_token
CODE_REPOS_JSON: str = _cfg.code_repos_json

__all__ = [
    "ADORSYS_BASE_URL",
    "ADORSYS_TOKEN",
    "ADORSYS_CODE_DIR",
    "RepoConfig",
    "REPOS",
    "ACTIVE_REPOS",
]

REPOS: list[RepoConfig] = load_repos(CODE_REPOS_JSON, "CODE_REPOS")
ACTIVE_REPOS: list[RepoConfig] = [r for r in REPOS if r.enabled]
