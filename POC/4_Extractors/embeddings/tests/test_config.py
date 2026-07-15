"""Tests for configuration loading and provider initialisation."""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest


class TestSettingsEmbedFields:
    """Embedding fields are present and default correctly."""

    def test_embed_model_name_default(self) -> None:
        from shared.config import settings

        assert settings.embed_model_name  # non-empty string

    def test_embed_timeout_is_positive_int(self) -> None:
        from shared.config import settings

        assert isinstance(settings.embed_timeout, int)
        assert settings.embed_timeout > 0

    def test_embed_max_retries_is_non_negative(self) -> None:
        from shared.config import settings

        assert settings.embed_max_retries >= 0

    def test_embed_batch_size_is_positive(self) -> None:
        from shared.config import settings

        assert settings.embed_batch_size > 0

    def test_embed_base_url_and_api_key_absent_when_env_unset(self) -> None:
        """Settings.from_env returns None for optional keys when env is blank."""
        from shared.config.settings import Settings

        clean_env = {
            k: v for k, v in os.environ.items()
            if k not in {"EMBED_BASE_URL", "EMBED_API_KEY"}
        }
        with patch.dict(os.environ, clean_env, clear=True):
            fresh = Settings.from_env()

        assert fresh.embed_base_url is None
        assert fresh.embed_api_key is None


class TestFactoryConfigurationError:
    """factory.create_client raises when required config is absent."""

    def test_raises_when_base_url_missing(self) -> None:
        from shared.config.loader import ConfigurationError
        from shared.config.settings import Settings

        clean_env = {
            k: v for k, v in os.environ.items()
            if k not in {"EMBED_BASE_URL", "EMBED_API_KEY"}
        }
        with patch.dict(os.environ, clean_env, clear=True):
            fresh_settings = Settings.from_env()

        import shared.config as _cfg
        original = _cfg.settings
        _cfg.settings = fresh_settings
        try:
            from importlib import reload
            import client.factory as _factory
            reload(_factory)
            with pytest.raises(ConfigurationError, match="EMBED_BASE_URL"):
                _factory.create_client()
        finally:
            _cfg.settings = original

    def test_raises_when_api_key_missing(self) -> None:
        from shared.config.loader import ConfigurationError
        from shared.config.settings import Settings

        env_override = {
            k: v for k, v in os.environ.items()
            if k != "EMBED_API_KEY"
        }
        env_override["EMBED_BASE_URL"] = "http://test"
        env_override.pop("EMBED_API_KEY", None)

        with patch.dict(os.environ, env_override, clear=True):
            fresh_settings = Settings.from_env()

        import shared.config as _cfg
        original = _cfg.settings
        _cfg.settings = fresh_settings
        try:
            from importlib import reload
            import client.factory as _factory
            reload(_factory)
            with pytest.raises(ConfigurationError, match="EMBED_API_KEY"):
                _factory.create_client()
        finally:
            _cfg.settings = original

