"""Central configuration package for the POC pipeline.

Usage in any pipeline stage::

    from shared.config import settings

    settings.log_level
    settings.gitlab_token
    settings.berlin_group_download_dir

Utilities for consumers that need to validate or parse configuration::

    from shared.config import require_env, parse_json_list, ConfigurationError
"""
from .loader import ConfigurationError, parse_json_list, require_env, validate_required_secrets
from .sources import ConfigSource
from .settings import Settings, settings

__all__ = [
    "settings",
    "Settings",
    "ConfigSource",
    "ConfigurationError",
    "require_env",
    "validate_required_secrets",
    "parse_json_list",
]
