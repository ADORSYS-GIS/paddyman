"""Async session manager for Neo4j operations."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Any

from .client import Neo4jClient


class Neo4jSessionManager:
    """Owns AsyncSession lifecycle for writer components."""

    def __init__(self, client: Neo4jClient) -> None:
        self._client = client

    @asynccontextmanager
    async def session(self) -> AsyncIterator[Any]:
        """Yield a Neo4j AsyncSession and close it via its context manager."""
        async with self._client.session() as session:
            yield session