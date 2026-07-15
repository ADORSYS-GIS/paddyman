"""Async writer for canonical entities."""
from __future__ import annotations

from entities.models import CanonicalEntity

from .serialization import entity_properties
from .session import Neo4jSessionManager


class EntityWriter:
    """Persist canonical entities using MERGE."""

    QUERY = """
    MERGE (e:Entity {id: $id})
    SET e += $properties
    RETURN e.id AS id
    """

    def __init__(self, sessions: Neo4jSessionManager) -> None:
        self._sessions = sessions

    async def write_entities(self, entities: list[CanonicalEntity]) -> int:
        """Write *entities* and return the number of MERGE operations requested."""
        if not entities:
            return 0
        async with self._sessions.session() as session:
            await session.execute_write(self._write_batch, entities)
        return len(entities)

    async def _write_batch(self, tx, entities: list[CanonicalEntity]) -> None:  # type: ignore[no-untyped-def]
        for entity in entities:
            props = entity_properties(entity)
            await tx.run(self.QUERY, id=entity.id, properties=props)