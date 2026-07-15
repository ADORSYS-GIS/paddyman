"""Neo4j index management for commonly queried entity properties."""
from __future__ import annotations

from .session import Neo4jSessionManager


class IndexManager:
    """Create graph indexes safely with IF NOT EXISTS."""

    QUERIES: tuple[str, ...] = (
        "CREATE INDEX entity_id_index IF NOT EXISTS FOR (e:Entity) ON (e.id)",
        "CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.type)",
        "CREATE INDEX entity_version_index IF NOT EXISTS FOR (e:Entity) ON (e.version_tag)",
        "CREATE INDEX entity_repository_index IF NOT EXISTS FOR (e:Entity) ON (e.repository)",
        "CREATE INDEX entity_module_index IF NOT EXISTS FOR (e:Entity) ON (e.module)",
    )

    def __init__(self, sessions: Neo4jSessionManager) -> None:
        self._sessions = sessions

    async def create_indexes(self) -> None:
        """Create all configured indexes."""
        async with self._sessions.session() as session:
            await session.execute_write(self._run_all)

    async def _run_all(self, tx) -> None:  # type: ignore[no-untyped-def]
        for query in self.QUERIES:
            await tx.run(query)