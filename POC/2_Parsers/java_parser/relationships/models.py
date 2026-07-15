"""Domain models for Java structural relationship extraction.

Represents directed edges in the type dependency graph produced by the
relationship extractor.  Designed for compatibility with downstream graph
normalisation stages.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RelationshipType(str, Enum):
    """Supported Java structural relationship kinds."""

    EXTENDS = "EXTENDS"
    IMPLEMENTS = "IMPLEMENTS"
    CALLS = "CALLS"


@dataclass
class JavaRelationship:
    """A single directed structural relationship between two Java types.

    Args:
        source:           Simple name of the source class.
        target:           Relationship target — a type name for EXTENDS /
                          IMPLEMENTS, or ``"receiver.method"`` for CALLS.
        relationship_type: Kind of relationship (EXTENDS / IMPLEMENTS / CALLS).
        package:          Java package of *source*.
        file_path:        Repository-relative source file path.
        repository:       Repository name (provenance).
        module:           Module label (provenance).
        source_method:    Enclosing method name for CALLS relationships;
                          ``None`` for structural relationships.
        target_method:    Called method name for CALLS relationships;
                          ``None`` for structural relationships.
        target_class:     Raw receiver expression for CALLS (variable or type);
                          equals *target* for EXTENDS / IMPLEMENTS.
        call_site_line:   Line number where call occurs (CALLS only).
        qualified_name:   Fully qualified name if resolvable (CALLS only).
        receiver_type:    Type of object receiving the call (CALLS only).
        arguments_count:  Number of arguments passed (CALLS only).
        is_static:        Boolean indicating static method call (CALLS only).
        is_constructor:   Boolean indicating constructor call (CALLS only).
    """

    source: str
    target: str
    relationship_type: str
    package: str
    file_path: str
    repository: str
    module: str
    source_method: str | None = None
    target_method: str | None = None
    target_class: str | None = None
    call_site_line: int | None = None
    qualified_name: str | None = None
    receiver_type: str | None = None
    arguments_count: int | None = None
    is_static: bool | None = None
    is_constructor: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict compatible with graph normalisation input."""
        result = {
            "source": self.source,
            "target": self.target,
            "type": self.relationship_type,
            "source_method": self.source_method,
            "target_method": self.target_method,
            "target_class": self.target_class,
            "package": self.package,
            "file_path": self.file_path,
            "repository": self.repository,
            "module": self.module,
        }
        # Add CALLS-specific fields if present
        if self.call_site_line is not None:
            result["call_site_line"] = self.call_site_line
        if self.qualified_name is not None:
            result["qualified_name"] = self.qualified_name
        if self.receiver_type is not None:
            result["receiver_type"] = self.receiver_type
        if self.arguments_count is not None:
            result["arguments_count"] = self.arguments_count
        if self.is_static is not None:
            result["is_static"] = self.is_static
        if self.is_constructor is not None:
            result["is_constructor"] = self.is_constructor
        return result
