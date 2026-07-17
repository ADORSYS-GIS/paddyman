"""Tests for LLM configuration loading from shared.config.settings."""
from __future__ import annotations

import pytest


class TestLLMConfigDefaults:
    """Verify that settings has LLM fields with correct defaults."""

    def test_llm_base_url_default(self, monkeypatch) -> None:
        monkeypatch.delenv("LLM_BASE_URL", raising=False)
        from shared.config.settings import Settings
        s = Settings.from_env()
        assert s.llm_base_url == "https://api.ai.camer.digital/v1"

    def test_llm_model_default(self, monkeypatch) -> None:
        monkeypatch.delenv("LLM_MODEL", raising=False)
        from shared.config.settings import Settings
        s = Settings.from_env()
        assert s.llm_model == "glm-5"

    def test_llm_api_key_none_when_unset(self, monkeypatch) -> None:
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        from shared.config.settings import Settings
        s = Settings.from_env()
        assert s.llm_api_key is None

    def test_llm_timeout_default(self, monkeypatch) -> None:
        monkeypatch.delenv("LLM_TIMEOUT", raising=False)
        from shared.config.settings import Settings
        s = Settings.from_env()
        assert s.llm_timeout == 60

    def test_llm_max_retries_default(self, monkeypatch) -> None:
        monkeypatch.delenv("LLM_MAX_RETRIES", raising=False)
        from shared.config.settings import Settings
        s = Settings.from_env()
        assert s.llm_max_retries == 3

    def test_llm_temperature_default(self, monkeypatch) -> None:
        monkeypatch.delenv("LLM_TEMPERATURE", raising=False)
        from shared.config.settings import Settings
        s = Settings.from_env()
        assert s.llm_temperature == 0.1

    def test_llm_max_tokens_default(self, monkeypatch) -> None:
        monkeypatch.delenv("LLM_MAX_TOKENS", raising=False)
        from shared.config.settings import Settings
        s = Settings.from_env()
        assert s.llm_max_tokens == 2048


class TestLLMConfigOverride:
    """Verify that env-var overrides are applied correctly."""

    def test_override_base_url(self, monkeypatch) -> None:
        monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
        from shared.config.settings import Settings
        s = Settings.from_env()
        assert s.llm_base_url == "http://localhost:11434/v1"

    def test_override_model(self, monkeypatch) -> None:
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")
        from shared.config.settings import Settings
        s = Settings.from_env()
        assert s.llm_model == "gpt-4o"

    def test_override_api_key(self, monkeypatch) -> None:
        monkeypatch.setenv("LLM_API_KEY", "sk-test-key")
        from shared.config.settings import Settings
        s = Settings.from_env()
        assert s.llm_api_key == "sk-test-key"

    def test_override_temperature(self, monkeypatch) -> None:
        monkeypatch.setenv("LLM_TEMPERATURE", "0.7")
        from shared.config.settings import Settings
        s = Settings.from_env()
        assert s.llm_temperature == 0.7
