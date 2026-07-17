"""Async writer for normalized relationships."""
from __future__ import annotations

from shared.models import Relationship

from .serialization import relationship_properties
from .session import Neo4jSessionManager


class RelationshipWriter:
    """Persist normalized relationships using MERGE."""

    QUERY = """
    MATCH (source:Entity {id: $source_id})
    MATCH (target:Entity {id: $target_id})
    MERGE (source)-[r:RELATIONSHIP {id: $id}]->(target)
    SET r += $properties
    RETURN r.id AS id
    """

    def __init__(self, sessions: Neo4jSessionManager) -> None:
        self._sessions = sessions

    async def write_relationships(self, relationships: list[Relationship]) -> int:
        """Write *relationships* and return the number of MERGE operations requested."""
        if not relationships:
            return 0
        async with self._sessions.session() as session:
            await session.execute_write(self._write_batch, relationships)
        return len(relationships)

    async def _write_batch(self, tx, relationships: list[Relationship]) -> None:  # type: ignore[no-untyped-def]
        for rel in relationships:
            props = relationship_properties(rel)
            await tx.run(
                self.QUERY,
                id=str(rel.id),
                source_id=props.get("source") or str(rel.source_entity_id),
                target_id=props.get("target") or str(rel.target_entity_id),
                properties=props,
            )