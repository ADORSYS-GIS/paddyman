"""Unit tests for shared.config."""
from __future__ import annotations

from pathlib import Path

import pytest

from shared.config import settings
from shared.config.settings import Settings


# ---------------------------------------------------------------------------
# Settings.from_env()
# ---------------------------------------------------------------------------


class TestSettingsDefaults:
    """Verify config.yml values apply when environment variables are unset."""

    def test_log_level_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        s = Settings.from_env()
        assert s.log_level == "INFO"

    def test_app_env_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("APP_ENV", raising=False)
        s = Settings.from_env()
        assert s.app_env == "development"

    def test_http_request_timeout_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("HTTP_REQUEST_TIMEOUT", raising=False)
        s = Settings.from_env()
        assert s.http_request_timeout == 120

    def test_http_retry_status_codes_default(self) -> None:
        s = Settings.from_env()
        assert 429 in s.http_retry_status_codes
        assert 503 in s.http_retry_status_codes

    def test_gitlab_token_none_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GITLAB_PERSONAL_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("GITLAB_TOKEN_ENV_VAR", raising=False)
        s = Settings.from_env()
        assert s.gitlab_token is None

    def test_openai_api_key_none_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        s = Settings.from_env()
        assert s.openai_api_key is None

    def test_summary_logging_enabled_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SUMMARY_LOGGING_ENABLED", raising=False)
        s = Settings.from_env()
        assert s.summary_logging_enabled is True

    def test_directory_fields_are_paths(self) -> None:
        s = Settings.from_env()
        assert isinstance(s.berlin_group_download_dir, Path)
        assert isinstance(s.yaml_spec_dir, Path)
        assert isinstance(s.adorsys_code_dir, Path)
        assert isinstance(s.docling_workspace_dir, Path)


class TestSettingsEnvOverride:
    """Verify that environment variables override config.yml correctly."""

    def test_log_level_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        s = Settings.from_env()
        assert s.log_level == "DEBUG"

    def test_app_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APP_ENV", "production")
        s = Settings.from_env()
        assert s.app_env == "production"

    def test_gitlab_token_read_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GITLAB_TOKEN_ENV_VAR", raising=False)
        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "tok-abc")
        s = Settings.from_env()
        assert s.gitlab_token == "tok-abc"

    def test_gitlab_token_env_var_indirection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GITLAB_TOKEN_ENV_VAR", "MY_CUSTOM_TOKEN")
        monkeypatch.setenv("MY_CUSTOM_TOKEN", "tok-custom")
        s = Settings.from_env()
        assert s.gitlab_token == "tok-custom"

    def test_summary_logging_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SUMMARY_LOGGING_ENABLED", "false")
        s = Settings.from_env()
        assert s.summary_logging_enabled is False

    def test_berlin_group_download_dir_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BERLIN_GROUP_DOWNLOAD_DIR", "/custom/downloads")
        s = Settings.from_env()
        assert s.berlin_group_download_dir == Path("/custom/downloads")


class TestSettingsImmutability:
    def test_settings_is_frozen(self) -> None:
        s = Settings.from_env()
        with pytest.raises((AttributeError, TypeError)):
            s.log_level = "DEBUG"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------


class TestSettingsSingleton:
    def test_singleton_is_settings_instance(self) -> None:
        assert isinstance(settings, Settings)

    def test_singleton_has_non_empty_log_level(self) -> None:
        assert settings.log_level


