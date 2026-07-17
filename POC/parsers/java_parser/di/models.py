"""Domain models for Spring dependency injection relationship extraction.

Designed for compatibility with downstream graph normalisation stages that
build directed dependency graphs from extracted relationships.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class InjectionType(str, Enum):
    """Supported Spring dependency injection mechanisms."""

    FIELD = "field"
    CONSTRUCTOR = "constructor"
    SETTER = "setter"


@dataclass
class DependencyRelationship:
    """A single Spring DI relationship between two Java types.

    Represents one directed ``source → target`` edge where *source* depends
    on *target* via a Spring injection mechanism.

    Args:
        source:           Simple name of the class declaring the dependency.
        target:           Simple name of the injected type.
        relationship_type: Relationship label for graph edges (always ``"USES"``).
        injection_type:   How the dependency is injected (field / constructor /
                          setter).
        field_name:       Identifier of the field or setter method that holds
                          the dependency (``None`` for constructor injection).
        package:          Java package of *source*.
        file_path:        Repository-relative source file path.
        repository:       Repository name (provenance).
        module:           Module label (provenance).
    """

    source: str
    target: str
    relationship_type: str
    injection_type: str
    package: str
    file_path: str
    repository: str
    module: str
    field_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict compatible with graph normalisation input."""
        return {
            "source": self.source,
            "target": self.target,
            "type": self.relationship_type,
            "injection_type": self.injection_type,
            "field_name": self.field_name,
            "package": self.package,
            "file_path": self.file_path,
            "repository": self.repository,
            "module": self.module,
        }
