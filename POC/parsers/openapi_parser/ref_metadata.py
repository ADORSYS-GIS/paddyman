"""$ref resolution tracking metadata.

Provides dataclasses to track which `$ref` references have been resolved,
detect circular references, and identify external refs.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RefMetadata:
    """Metadata about a resolved $ref.

    Attributes:
        ref_path:      Original $ref string (e.g., "#/components/schemas/Account").
        dereferenced:  True if the ref was successfully resolved.
        is_external:   True if the ref points to an external file or URL.
        circular:      True if a circular reference was detected.
    """

    ref_path: str
    dereferenced: bool = False
    is_external: bool = False
    circular: bool = False


@dataclass
class SchemaRefInfo:
    """Complete $ref tracking information for a schema entity.

    Attributes:
        is_reference:   True if this entity is itself a $ref to another definition.
        ref_path:       Original $ref path if is_reference is True.
        refs:           List of all $ref paths contained within this schema.
        external_refs:  List of external $ref paths only.
        circular_refs:  List of $ref paths that form circular references.
        dereferenced:   True if all refs have been successfully resolved.
    """

    is_reference: bool = False
    ref_path: str | None = None
    refs: list[str] = field(default_factory=list)
    external_refs: list[str] = field(default_factory=list)
    circular_refs: list[str] = field(default_factory=list)
    dereferenced: bool = True

