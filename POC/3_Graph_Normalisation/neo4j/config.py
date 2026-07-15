"""Neo4j configuration loaded through shared.config."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shared.config import require_env, settings


@dataclass(frozen=True)
class Neo4jSettings:
    """Connection settings for the Neo4j writer."""

    uri: str
    username: str
    password: str
    database: str

    @classmethod
    def from_shared_config(cls, source: Any = settings) -> "Neo4jSettings":
        """Load Neo4j settings from shared configuration or shared env loader."""
        return cls(
            uri=_value(source, "neo4j_uri", "NEO4J_URI"),
            username=_value(source, "neo4j_username", "NEO4J_USERNAME"),
            password=_value(source, "neo4j_password", "NEO4J_PASSWORD"),
            database=_value(source, "neo4j_database", "NEO4J_DATABASE"),
        )


def _value(source: Any, attr: str, env_name: str) -> str:
    value = getattr(source, attr, None)
    if value is not None and str(value).strip():
        return str(value).strip()
    return require_env(env_name)