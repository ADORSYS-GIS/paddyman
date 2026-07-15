"""Tests for config.yml and .env source merging."""
from __future__ import annotations

from pathlib import Path

import pytest

from shared.config import ConfigurationError, validate_required_secrets
from shared.config.loader import load_yaml_config
from shared.config.settings import Settings


def _config(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "config.yml"
    path.write_text(body, encoding="utf-8")
    return path


def test_non_sensitive_values_load_from_yaml(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    config = _config(tmp_path, "logging:\n  level: WARNING\nembedding:\n  model_name: local-model\n")
    settings = Settings.from_sources(config)
    assert settings.log_level == "WARNING"
    assert settings.embed_model_name == "local-model"


def test_env_overrides_yaml(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    config = _config(tmp_path, "logging:\n  level: WARNING\n")
    assert Settings.from_sources(config).log_level == "DEBUG"


def test_secret_loads_from_env_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    config = _config(tmp_path, "llm:\n  model: test-model\n")
    env = tmp_path / ".env"
    env.write_text("LLM_API_KEY=secret-from-env\n", encoding="utf-8")
    assert Settings.from_sources(config, env).llm_api_key == "secret-from-env"


def test_settings_exposes_all_loaded_sources(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("CUSTOM_SECRET", raising=False)
    config = _config(tmp_path, "custom:\n  feature: enabled\n")
    env = tmp_path / ".env"
    env.write_text("CUSTOM_SECRET=secret-value\n", encoding="utf-8")

    settings = Settings.from_sources(config, env)

    assert settings.raw["custom"]["feature"] == "enabled"
    assert settings.env["CUSTOM_SECRET"] == "secret-value"
    assert settings.get("custom.feature") == "enabled"
    assert settings.get("custom.feature", env="CUSTOM_SECRET") == "secret-value"


def test_missing_required_secret_is_detected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISSING_SECRET", raising=False)
    with pytest.raises(ConfigurationError, match="MISSING_SECRET"):
        validate_required_secrets(["MISSING_SECRET"])


def test_invalid_yaml_raises_configuration_error(tmp_path) -> None:  # type: ignore[no-untyped-def]
    config = _config(tmp_path, "logging: [broken\n")
    with pytest.raises(ConfigurationError, match="Cannot load application config"):
        load_yaml_config(config)