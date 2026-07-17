"""Domain models for the Java AST extraction phase.

These models carry the structured metadata produced by parsing Java source
files.  They are designed to be compatible with downstream extraction stages
that build knowledge graphs from parsed type information.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class JavaDeclarationType(str, Enum):
    """Supported top-level Java type declaration kinds."""

    CLASS = "class"
    INTERFACE = "interface"
    ENUM = "enum"


@dataclass
class JavaAnnotation:
    """A single annotation applied to a Java type, method, or field.

    Args:
        name:       Annotation simple name without the ``@`` prefix (e.g. ``"Override"``).
        value:      Raw text of the primary (unnamed) annotation argument, if present.
        attributes: Named element–value pairs extracted from the annotation body.
    """

    name: str
    value: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "value": self.value, "attributes": self.attributes}


@dataclass(frozen=True)
class SourceLocation:
    """Zero-based byte-offset source position.

    Line and column numbers follow the tree-sitter convention:
    both are zero-based.  Callers may add 1 when reporting to users.
    """

    start_line: int
    start_col: int
    end_line: int
    end_col: int

    def to_dict(self) -> dict[str, int]:
        return {
            "start_line": self.start_line,
            "start_col": self.start_col,
            "end_line": self.end_line,
            "end_col": self.end_col,
        }


@dataclass
class JavaImportDeclaration:
    """A single Java import declaration.

    Args:
        name:          Fully-qualified import name (e.g. ``"java.util.List"``).
        is_static:     True for static imports.
        is_wildcard:   True for wildcard imports (``.*``).
        location:      Source position within the file.
        file_path:     Repository-relative path to the source file.
        repository:    Repository name (from discovery).
        module:        Module label (from discovery).
        package:       Package of the file containing this import.
    """

    name: str
    is_static: bool = False
    is_wildcard: bool = False
    location: SourceLocation = field(
        default_factory=lambda: SourceLocation(0, 0, 0, 0)
    )
    file_path: str = ""
    repository: str = ""
    module: str = ""
    package: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary suitable for JSON output."""
        return {
            "name": self.name,
            "is_static": self.is_static,
            "is_wildcard": self.is_wildcard,
            "location": self.location.to_dict(),
            "file_path": self.file_path,
            "repository": self.repository,
            "module": self.module,
            "package": self.package,
        }

    @property
    def imported_name(self) -> str:
        """Extract the simple name from the fully-qualified import.

        Returns the last component for regular imports, or the second-to-last
        for wildcard imports.
        """
        if self.is_wildcard:
            parts = self.name.rstrip(".*").split(".")
            return parts[-1] if parts else ""
        parts = self.name.split(".")
        return parts[-1] if parts else ""


@dataclass
class JavaTypeDeclaration:
    """A single top-level Java type declaration (class, interface, or enum).

    Args:
        type:         Declaration kind.
        name:         Simple (unqualified) type name.
        package:      Package of the enclosing file.
        modifiers:    Access / non-access modifiers (e.g. ``["public", "abstract"]``).
        superclass:   Simple name of the extended class (classes only).
        interfaces:   Simple names of implemented or extended interfaces.
        location:     Source position within the file.
        file_path:    Repository-relative path to the source file.
        repository:   Repository name (from discovery).
        module:       Module label (from discovery).
    """

    type: JavaDeclarationType
    name: str
    package: str
    modifiers: list[str] = field(default_factory=list)
    superclass: str | None = None
    interfaces: list[str] = field(default_factory=list)
    annotations: list["JavaAnnotation"] = field(default_factory=list)
    location: SourceLocation = field(
        default_factory=lambda: SourceLocation(0, 0, 0, 0)
    )
    file_path: str = ""
    repository: str = ""
    module: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary suitable for JSON output."""
        return {
            "type": self.type.value,
            "name": self.name,
            "package": self.package,
            "modifiers": self.modifiers,
            "superclass": self.superclass,
            "interfaces": self.interfaces,
            "annotations": [a.to_dict() for a in self.annotations],
            "location": self.location.to_dict(),
            "file_path": self.file_path,
            "repository": self.repository,
            "module": self.module,
        }


@dataclass
class JavaFileAst:
    """Parsed AST metadata for a single Java source file.

    Args:
        file_path:          Repository-relative path to the source file.
        repository:         Repository name.
        module:             Module label.
        package:            Package declared in this file.
        imports:            Fully-qualified import names (strings for backward compat).
        import_declarations: Structured import declarations.
        declarations:       Extracted type declarations.
        has_errors:         True when the parser detected syntax errors.
        error_message:      Human-readable parse error description, when applicable.
    """

    file_path: str
    repository: str
    module: str
    package: str
    imports: list[str] = field(default_factory=list)
    import_declarations: list[JavaImportDeclaration] = field(default_factory=list)
    declarations: list[JavaTypeDeclaration] = field(default_factory=list)
    has_errors: bool = False
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary suitable for JSON output."""
        return {
            "file_path": self.file_path,
            "repository": self.repository,
            "module": self.module,
            "package": self.package,
            "imports": self.imports,
            "import_declarations": [d.to_dict() for d in self.import_declarations],
            "declarations": [d.to_dict() for d in self.declarations],
            "has_errors": self.has_errors,
            "error_message": self.error_message,
        }
