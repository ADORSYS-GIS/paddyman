"""High-level writer for the normalized graph."""
from __future__ import annotations

from entities.models import CanonicalEntity
from shared.models import Relationship

from .client import Neo4jClient
from .constraints import ConstraintManager
from .entity_writer import EntityWriter
from .indexes import IndexManager
from .relationship_writer import RelationshipWriter
from .session import Neo4jSessionManager


class GraphWriter:
    """Coordinate schema setup and graph persistence."""

    def __init__(self, client: Neo4jClient) -> None:
        sessions = Neo4jSessionManager(client)
        self.constraints = ConstraintManager(sessions)
        self.indexes = IndexManager(sessions)
        self.entities = EntityWriter(sessions)
        self.relationships = RelationshipWriter(sessions)

    async def setup_schema(self) -> None:
        """Create constraints and indexes safely."""
        await self.constraints.create_constraints()
        await self.indexes.create_indexes()

    async def write_graph(
        self,
        entities: list[CanonicalEntity],
        relationships: list[Relationship],
    ) -> dict[str, int]:
        """Persist normalized graph entities first, then relationships."""
        entity_count = await self.entities.write_entities(entities)
        relationship_count = await self.relationships.write_relationships(relationships)
        return {"entities": entity_count, "relationships": relationship_count}