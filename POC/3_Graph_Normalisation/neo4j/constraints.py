"""Neo4j constraint management for normalized graph persistence."""
from __future__ import annotations

from .session import Neo4jSessionManager


class ConstraintManager:
    """Create graph constraints safely with IF NOT EXISTS."""

    ENTITY_ID = """
    CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
    FOR (e:Entity) REQUIRE e.id IS UNIQUE
    """
    CANONICAL_ID = """
    CREATE CONSTRAINT entity_canonical_id_unique IF NOT EXISTS
    FOR (e:Entity) REQUIRE e.canonical_id IS UNIQUE
    """

    def __init__(self, sessions: Neo4jSessionManager) -> None:
        self._sessions = sessions

    async def create_constraints(self) -> None:
        """Create all entity uniqueness constraints."""
        async with self._sessions.session() as session:
            await session.execute_write(self._run_all)

    async def _run_all(self, tx) -> None:  # type: ignore[no-untyped-def]
        for query in (self.ENTITY_ID, self.CANONICAL_ID):
            await tx.run(query)