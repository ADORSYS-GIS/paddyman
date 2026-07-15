"""Typed central settings merged from config.yml and environment secrets."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .sources import ConfigSource
from .values import build_settings_values

_POC_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """Project-wide immutable configuration."""

    app_env: str
    log_level: str
    log_format: str
    summary_logging_enabled: bool
    http_request_timeout: int
    http_connect_timeout: int
    http_retries: int
    http_retry_backoff: float
    http_chunk_size: int
    http_user_agent: str
    http_retry_status_codes: frozenset[int]
    scraper_timeout_ms: int
    scraper_post_load_wait_ms: int
    gitlab_base_url: str
    gitlab_token: str | None
    adorsys_base_url: str
    adorsys_token: str | None
    git_clone_depth: int
    berlin_group_download_dir: Path
    markdown_spec_dir: Path
    yaml_spec_dir: Path
    adorsys_code_dir: Path
    pdf_sources_json: str
    yaml_repos_json: str
    code_repos_json: str
    java_parser_source_dir: Path
    parser_output_dir: Path
    extraction_input_dir: Path
    docling_workspace_dir: Path
    docling_chunks_dir: Path
    docling_downloads_dir: Path
    docling_picture_mode: str
    docling_max_workers: int
    openai_api_key: str | None
    embed_base_url: str | None
    embed_model_name: str
    embed_api_key: str | None
    embed_timeout: int
    embed_max_retries: int
    embed_batch_size: int
    embed_max_chars: int
    extraction_max_records: int
    extraction_output_dir: Path | None
    llm_base_url: str
    llm_model: str
    llm_api_key: str | None
    llm_timeout: int
    llm_max_retries: int
    llm_temperature: float
    llm_max_tokens: int
    graph_normalisation_input_dir: Path
    graph_normalisation_output_dir: Path
    neo4j_uri: str | None
    neo4j_username: str | None
    neo4j_password: str | None
    neo4j_database: str
    raw: dict[str, Any]
    env: dict[str, str]

    @classmethod
    def from_env(cls) -> "Settings":
        return cls.from_sources(_POC_ROOT / "config.yml", _POC_ROOT / ".env")

    @classmethod
    def from_sources(cls, config_path: Path, env_path: Path | None = None) -> "Settings":
        source = ConfigSource.load(config_path, env_path)
        return cls(**build_settings_values(source.raw), raw=source.raw, env=source.env)

    def get(self, path: str, default: Any = None, env: str | None = None) -> Any:
        """Return an env override or dotted config.yml value from the autoloaded sources."""
        return ConfigSource(self.raw, self.env).get(path, default, env)


settings: Settings = Settings.from_env()