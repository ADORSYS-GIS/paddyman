"""Tests for shared.config helper functions."""
from __future__ import annotations

import json

import pytest

from shared.config import ConfigurationError, parse_json_list, require_env


class TestRequireEnv:
    def test_returns_value_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEST_REQUIRED_VAR", "hello")
        assert require_env("TEST_REQUIRED_VAR") == "hello"

    def test_raises_when_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("TEST_REQUIRED_VAR", raising=False)
        with pytest.raises(ConfigurationError, match="TEST_REQUIRED_VAR"):
            require_env("TEST_REQUIRED_VAR")

    def test_raises_when_blank(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEST_REQUIRED_VAR", "   ")
        with pytest.raises(ConfigurationError, match="TEST_REQUIRED_VAR"):
            require_env("TEST_REQUIRED_VAR")


class TestParseJsonList:
    def test_parses_valid_json_array(self) -> None:
        result = parse_json_list(json.dumps([{"name": "A"}, {"name": "B"}]), "MY_VAR")
        assert len(result) == 2
        assert result[0]["name"] == "A"

    def test_empty_raw_returns_empty_list(self) -> None:
        assert parse_json_list("", "MY_VAR") == []

    def test_whitespace_raw_returns_empty_list(self) -> None:
        assert parse_json_list("   ", "MY_VAR") == []

    def test_invalid_json_raises_configuration_error(self) -> None:
        with pytest.raises(ConfigurationError, match="invalid JSON"):
            parse_json_list("{not valid json}", "MY_VAR")

    def test_json_object_raises_configuration_error(self) -> None:
        with pytest.raises(ConfigurationError, match="JSON array"):
            parse_json_list('{"key": "value"}', "MY_VAR")

    def test_json_string_raises_configuration_error(self) -> None:
        with pytest.raises(ConfigurationError, match="JSON array"):
            parse_json_list('"just a string"', "MY_VAR")