"""Domain models for Spring Boot resource file parsing."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ResourceFileType(str, Enum):
    """Recognised resource file types."""

    PROPERTIES = "properties"
    YAML = "yaml"
    XML = "xml"


class XmlType(str, Enum):
    """Detected XML sub-type."""

    POM = "pom"
    LIQUIBASE = "liquibase"
    SPRING = "spring"
    GENERIC = "generic"


@dataclass
class ResourceFile:
    """A discovered resource file record (before parsing).

    Args:
        repository:    Repository directory name.
        module:        Module label derived from the file's location.
        file:          Bare filename.
        relative_path: Path relative to the repository root.
        file_type:     One of the :class:`ResourceFileType` string values.
    """

    repository: str
    module: str
    file: str
    relative_path: str
    file_type: str


@dataclass
class ParsedResource:
    """A fully parsed resource file with extracted metadata.

    Args:
        repository:    Repository directory name.
        module:        Module label.
        file:          Bare filename.
        relative_path: Path relative to the repository root.
        file_type:     One of the :class:`ResourceFileType` string values.
        xml_type:      XML sub-type value, or ``None`` for non-XML files.
        content:       Parser-specific extracted data.
        parse_errors:  Non-fatal error messages collected during parsing.
    """

    repository: str
    module: str
    file: str
    relative_path: str
    file_type: str
    xml_type: str | None
    content: dict[str, Any]
    parse_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary suitable for JSON output."""
        result: dict[str, Any] = {
            "repository": self.repository,
            "module": self.module,
            "file": self.file,
            "relative_path": self.relative_path,
            "type": self.file_type,
        }
        if self.xml_type is not None:
            result["xml_type"] = self.xml_type
        result.update(self.content)
        return result
