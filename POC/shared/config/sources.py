"""Autoload and expose merged configuration sources."""
from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .loader import (
    get_config_value,
    load_dotenv,
    load_yaml_config,
    ConfigurationError,
)


@dataclass(frozen=True)
class ConfigSource:
    """Merged view of config.yml plus .env/environment values."""

    raw: dict[str, Any]
    env: dict[str, str]

    @classmethod
    def load(cls, config_path: Path, env_path: Path | None = None) -> "ConfigSource":
        if env_path is not None:
            load_dotenv(env_path)
        try:
            raw = load_yaml_config(config_path)
        except ConfigurationError:
            logging.getLogger(__name__).warning(
                "Application config %s not found; falling back to empty config",
                config_path,
            )
            raw = {}
        return cls(raw=raw, env=dict(os.environ))

    def get(self, path: str, default: Any = None, env: str | None = None) -> Any:
        """Return an env override or dotted config.yml value."""
        if env and self.env.get(env) not in (None, ""):
            return self.env[env]
        return get_config_value(self.raw, path, default)