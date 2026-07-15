"""Async Neo4j client and connection management."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

from .config import Neo4jSettings

DriverFactory = Callable[[str, tuple[str, str]], Any]


class Neo4jClient:
    """Thin wrapper around the Neo4j Python Driver async driver."""

    def __init__(
        self,
        config: Neo4jSettings | None = None,
        driver_factory: DriverFactory | None = None,
    ) -> None:
        self.config = config if config is not None else Neo4jSettings.from_shared_config()
        self._factory = driver_factory if driver_factory is not None else _default_factory
        self.driver = self._factory(self.config.uri, (self.config.username, self.config.password))

    async def verify_connectivity(self) -> None:
        """Verify that the configured Neo4j server is reachable."""
        await self.driver.verify_connectivity()

    def session(self) -> Any:
        """Create an AsyncSession for the configured database."""
        return self.driver.session(database=self.config.database)

    async def close(self) -> None:
        """Close the underlying async driver."""
        await self.driver.close()


def _default_factory(uri: str, auth: tuple[str, str]) -> Any:
    """Load the official Neo4j driver even when this package is named neo4j."""
    local_package = Path(__file__).resolve().parents[1]
    removed_paths = [p for p in sys.path if Path(p).resolve() == local_package]
    existing = sys.modules.pop("neo4j", None)
    for path in removed_paths:
        sys.path.remove(path)
    try:
        from neo4j import AsyncGraphDatabase  # type: ignore

        return AsyncGraphDatabase.driver(uri, auth=auth)
    finally:
        for path in removed_paths:
            sys.path.insert(0, path)
        if existing is not None:
            sys.modules["neo4j"] = existing