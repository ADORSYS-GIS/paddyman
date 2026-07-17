"""Build typed Settings constructor values from merged configuration sources."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .loader import get_config_value

_POC_ROOT = Path(__file__).resolve().parents[2]


def build_settings_values(config: dict[str, Any]) -> dict[str, Any]:
    e = os.environ.get

    def value(env_name: str, key: str, default: Any = None) -> Any:
        env_value = e(env_name)
        return env_value if env_value not in (None, "") else get_config_value(config, key, default)

    gitlab_token_var = str(value("GITLAB_TOKEN_ENV_VAR", "git.gitlab_token_env_var", "GITLAB_PERSONAL_ACCESS_TOKEN"))
    adorsys_token_var = str(value("ADORSYS_TOKEN_ENV_VAR", "git.adorsys_token_env_var", "ADORSYS_GITLAB_TOKEN"))
    extraction_output = value("EXTRACTION_OUTPUT_DIR", "extraction.output_dir")

    return {
        "app_env": str(value("APP_ENV", "application.env", "development")),
        "log_level": str(value("LOG_LEVEL", "logging.level", "INFO")),
        "log_format": str(value("LOG_FORMAT", "logging.format", "%(asctime)s %(levelname)s %(name)s — %(message)s")),
        "summary_logging_enabled": _bool(value("SUMMARY_LOGGING_ENABLED", "logging.summary_enabled", True)),
        "http_request_timeout": int(value("HTTP_REQUEST_TIMEOUT", "http.request_timeout", 120)),
        "http_connect_timeout": int(value("HTTP_CONNECT_TIMEOUT", "http.connect_timeout", 30)),
        "http_retries": int(value("HTTP_RETRIES", "http.retries", 3)),
        "http_retry_backoff": float(value("HTTP_RETRY_BACKOFF", "http.retry_backoff", 1.5)),
        "http_chunk_size": int(value("HTTP_CHUNK_SIZE", "http.chunk_size", 8192)),
        "http_user_agent": str(value("HTTP_USER_AGENT", "http.user_agent", "")),
        "http_retry_status_codes": _int_set(value("HTTP_RETRY_STATUS_CODES", "http.retry_status_codes", [429, 500, 502, 503, 504])),
        "scraper_timeout_ms": int(value("SCRAPER_TIMEOUT_MS", "scraper.timeout_ms", 90000)),
        "scraper_post_load_wait_ms": int(value("SCRAPER_POST_LOAD_WAIT_MS", "scraper.post_load_wait_ms", 12000)),
        "gitlab_base_url": str(value("GITLAB_BASE_URL", "git.gitlab_base_url", "https://gitlab.com")),
        "gitlab_token": e(gitlab_token_var) or None,
        "adorsys_base_url": str(value("ADORSYS_GITLAB_BASE_URL", "git.adorsys_base_url", "https://git.adorsys.de")),
        "adorsys_token": e(adorsys_token_var) or None,
        "git_clone_depth": int(value("GIT_CLONE_DEPTH", "git.clone_depth", 0)),
        "berlin_group_download_dir": _abspath(value("BERLIN_GROUP_DOWNLOAD_DIR", "paths.berlin_group_download_dir")),
        "markdown_spec_dir": _abspath(value("MARKDOWN_SPEC_DIR", "paths.berlin_group_specification_md_files")),
        "yaml_spec_dir": _abspath(value("YAML_SPEC_DIR", "paths.yaml_spec_dir")),
        "adorsys_code_dir": _abspath(value("ADORSYS_CODE_DIR", "paths.adorsys_code_dir")),
        "pdf_sources_json": e("PDF_SOURCES") or _json(get_config_value(config, "sources.pdf", [])),
        "yaml_repos_json": e("YAML_REPOS") or _json(get_config_value(config, "sources.yaml_repos", [])),
        "code_repos_json": e("CODE_REPOS") or _json(get_config_value(config, "sources.code_repos", [])),
        "java_parser_source_dir": _abspath(value("JAVA_PARSER_SOURCE_DIR", "parser.java_source_dir")),
        "parser_output_dir": _abspath(value("PARSER_OUTPUT_DIR", "parser.output_dir")),
        "extraction_input_dir": _abspath(value("EXTRACTION_INPUT_DIR", "extraction.input_dir")),
        "docling_workspace_dir": _abspath(value("DOCLING_WORKSPACE_DIR", "docling.workspace_dir")),
        "docling_chunks_dir": _abspath(value("DOCLING_CHUNKS_DIR", "docling.chunks_dir")),
        "docling_downloads_dir": _abspath(value("DOCLING_DOWNLOADS_DIR", "docling.downloads_dir")),
        "docling_picture_mode": str(value("DOCLING_PICTURE_MODE", "docling.picture_mode", "none")),
        "docling_max_workers": int(value("DOCLING_MAX_WORKERS", "docling.max_workers", 0)),
        "openai_api_key": e("OPENAI_API_KEY") or None,
        "embed_base_url": str(value("EMBED_BASE_URL", "embedding.base_url", "")) or None,
        "embed_model_name": str(value("EMBED_MODEL_NAME", "embedding.model_name", "qwen3-embedding-8b")),
        "embed_api_key": e("EMBED_API_KEY") or None,
        "embed_timeout": int(value("EMBED_TIMEOUT", "embedding.timeout", 60)),
        "embed_max_retries": int(value("EMBED_MAX_RETRIES", "embedding.max_retries", 3)),
        "embed_batch_size": int(value("EMBED_BATCH_SIZE", "embedding.batch_size", 32)),
        "embed_max_chars": int(value("EMBED_MAX_CHARS", "embedding.max_chars", 100000)),
        "extraction_max_records": int(value("EXTRACTION_MAX_RECORDS", "extraction.max_records", 0)),
        "extraction_output_dir": _abspath(extraction_output) if extraction_output else None,
        "llm_base_url": str(value("LLM_BASE_URL", "llm.base_url", "")),
        "llm_model": str(value("LLM_MODEL", "llm.model", "glm-4.7-flash")),
        "llm_api_key": e("LLM_API_KEY") or None,
        "llm_timeout": int(value("LLM_TIMEOUT", "llm.timeout", 60)),
        "llm_max_retries": int(value("LLM_MAX_RETRIES", "llm.max_retries", 3)),
        "llm_temperature": float(value("LLM_TEMPERATURE", "llm.temperature", 0.1)),
        "llm_max_tokens": int(value("LLM_MAX_TOKENS", "llm.max_tokens", 2048)),
        "use_stable_uuids": _bool(value("USE_STABLE_UUIDS", "identifiers.use_stable_uuids", True)),
        "graph_normalisation_input_dir": _abspath(value("GRAPH_NORMALISATION_INPUT_DIR", "graph.input_dir")),
        "graph_normalisation_output_dir": _abspath(value("GRAPH_NORMALISATION_OUTPUT_DIR", "graph.output_dir")),
        "neo4j_uri": str(value("NEO4J_URI", "neo4j.uri", "")) or None,
        "neo4j_username": e("NEO4J_USERNAME") or e("NEO4J_USER") or None,
        "neo4j_password": e("NEO4J_PASSWORD") or None,
        "neo4j_database": str(value("NEO4J_DATABASE", "neo4j.database", "neo4j")),
    }


def _abspath(value: str | Path | None) -> Path:
    path = Path(str(value or ""))
    return path if path.is_absolute() else _POC_ROOT / path


def _json(value: Any) -> str:
    return value if isinstance(value, str) else json.dumps(value or [])


def _bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _int_set(value: Any) -> frozenset[int]:
    if isinstance(value, str):
        return frozenset(int(item.strip()) for item in value.split(",") if item.strip())
    return frozenset(int(item) for item in value)