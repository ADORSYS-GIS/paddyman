"""Central configuration loading helpers."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when a required configuration value is absent or invalid."""


def require_env(name: str) -> str:
    """Return a non-blank secret from the environment."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigurationError(
            f"Required environment variable '{name}' is not set. "
            "Copy POC/.env.example to POC/.env and supply the value."
        )
    return value


def validate_required_secrets(names: list[str]) -> None:
    """Raise when any required secret environment variable is missing."""
    missing = [name for name in names if not os.environ.get(name, "").strip()]
    if missing:
        joined = ", ".join(sorted(missing))
        raise ConfigurationError(f"Missing required secret(s): {joined}")


def load_dotenv(env_path: Path) -> None:
    """Load secrets from *.env* without overriding exported environment values."""
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, raw_value = line.split("=", 1)
        name = name.strip()
        if not name or name in os.environ:
            continue
        os.environ[name] = _clean_env_value(raw_value)


def _clean_env_value(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
        return cleaned[1:-1]
    return cleaned


def load_yaml_config(path: Path) -> dict[str, Any]:
    """Load non-sensitive application configuration from YAML."""
    if not path.exists():
        raise ConfigurationError(f"Application config not found: {path}")
    try:
        import yaml

        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ConfigurationError(f"Cannot load application config {path}: {exc}") from exc
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ConfigurationError(f"Application config {path} must contain a YAML mapping")
    return payload


def get_config_value(config: dict[str, Any], path: str, default: Any = None) -> Any:
    """Return a dotted-path value from *config*."""
    value: Any = config
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def parse_json_list(raw: str, var_name: str) -> list[dict]:
    """Parse a JSON-encoded list from *raw*, the value of environment variable *var_name*.

    Returns an empty list with a logged warning when *raw* is blank.

    Raises:
        ConfigurationError: on malformed JSON or when the decoded value is not a list.
    """
    if not raw.strip():
        logger.warning(
            "Environment variable '%s' is not set — no entries will be processed. "
            "See POC/.env.example for the expected format.",
            var_name,
        )
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"'{var_name}' contains invalid JSON: {exc}. "
            "Consult POC/.env.example for the expected format."
        ) from exc

    if not isinstance(data, list):
        raise ConfigurationError(
            f"'{var_name}' must be a JSON array; got {type(data).__name__}."
        )

    return data  # type: ignore[return-value]
