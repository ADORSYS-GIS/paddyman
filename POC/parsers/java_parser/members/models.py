"""Domain models for extracted Java class members.

These models carry the structured member metadata produced by the member
extraction phase and are designed for compatibility with downstream graph
normalisation stages.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from java_parser.java_ast.models import JavaAnnotation, SourceLocation  # noqa: F401 – re-exported for field default

AnnotationValue = JavaAnnotation | str


@dataclass(frozen=True)
class JavaParameter:
    """A single method or constructor parameter.

    Args:
        name:       Parameter identifier.
        type:       Fully-rendered type string (e.g. ``"List<String>"``, ``"int[]"``).
        is_vararg:  True when the parameter uses varargs (``...``).
        annotations: Annotation objects applied to the parameter.
        position:   Zero-based index of the parameter within the formal list.
    """

    name: str
    type: str
    is_vararg: bool = False
    annotations: list[AnnotationValue] = field(default_factory=list)
    position: int = 0

    def to_dict(self, imports: list[str] | None = None) -> dict[str, Any]:
        # Local import to avoid cycles in module import graph
        from java_parser.java_ast.models import JavaAnnotation as _JavaAnnotation
        from java_parser.annotation_normalizer import normalize_annotations_obj

        if imports is None:
            anns = [a.to_dict() if isinstance(a, _JavaAnnotation) else a for a in self.annotations]
        else:
            anns = normalize_annotations_obj(self.annotations, imports)

        return {
            "name": self.name,
            "type": self.type,
            "is_vararg": self.is_vararg,
            "position": self.position,
            "annotations": anns,
        }


@dataclass
class JavaField:
    """A field declared in a Java class or interface.

    Args:
        name:       Field identifier.
        type:       Fully-rendered type string.
        modifiers:  Access and non-access modifiers.
        class_name: Simple name of the enclosing class.
        package:    Package of the enclosing file.
        file_path:  Repository-relative path to the source file.
        repository: Repository name.
        module:     Module label.
    """

    name: str
    type: str
    modifiers: list[str]
    class_name: str
    package: str
    file_path: str
    repository: str
    module: str
    annotations: list[AnnotationValue] = field(default_factory=list)
    location: SourceLocation = field(
        default_factory=lambda: SourceLocation(0, 0, 0, 0)
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "field",
            "name": self.name,
            "field_type": self.type,
            "modifiers": self.modifiers,
            "annotations": [
                a.to_dict() if isinstance(a, JavaAnnotation) else a
                for a in self.annotations
            ],
            "class": self.class_name,
            "package": self.package,
            "file_path": self.file_path,
            "repository": self.repository,
            "module": self.module,
            "location": self.location.to_dict(),
        }


@dataclass
class JavaMethod:
    """A method declared in a Java class or interface.

    Args:
        name:        Method identifier.
        return_type: Fully-rendered return type string.
        modifiers:   Access and non-access modifiers.
        parameters:  Ordered list of formal parameters.
        class_name:  Simple name of the enclosing class.
        package:     Package of the enclosing file.
        file_path:   Repository-relative path to the source file.
        repository:  Repository name.
        module:      Module label.
        location:    Source position within the file.
    """

    name: str
    return_type: str
    modifiers: list[str]
    parameters: list[JavaParameter]
    class_name: str
    package: str
    file_path: str
    repository: str
    module: str
    annotations: list[AnnotationValue] = field(default_factory=list)
    location: SourceLocation = field(
        default_factory=lambda: SourceLocation(0, 0, 0, 0)
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "method",
            "name": self.name,
            "return_type": self.return_type,
            "modifiers": self.modifiers,
            "annotations": [
                a.to_dict() if isinstance(a, JavaAnnotation) else a
                for a in self.annotations
            ],
            "parameters": [p.to_dict() for p in self.parameters],
            "class": self.class_name,
            "package": self.package,
            "file_path": self.file_path,
            "repository": self.repository,
            "module": self.module,
            "location": self.location.to_dict(),
        }


@dataclass
class JavaConstructor:
    """A constructor declared in a Java class.

    Args:
        name:       Constructor name (same as the class name).
        modifiers:  Access modifiers.
        parameters: Ordered list of formal parameters.
        class_name: Simple name of the enclosing class.
        package:    Package of the enclosing file.
        file_path:  Repository-relative path to the source file.
        repository: Repository name.
        module:     Module label.
        location:   Source position within the file.
    """

    name: str
    modifiers: list[str]
    parameters: list[JavaParameter]
    class_name: str
    package: str
    file_path: str
    repository: str
    module: str
    annotations: list[AnnotationValue] = field(default_factory=list)
    location: SourceLocation = field(
        default_factory=lambda: SourceLocation(0, 0, 0, 0)
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "constructor",
            "name": self.name,
            "modifiers": self.modifiers,
            "annotations": [
                a.to_dict() if isinstance(a, JavaAnnotation) else a
                for a in self.annotations
            ],
            "parameters": [p.to_dict() for p in self.parameters],
            "class": self.class_name,
            "package": self.package,
            "file_path": self.file_path,
            "repository": self.repository,
            "module": self.module,
            "location": self.location.to_dict(),
        }


@dataclass
class ClassMembers:
    """All extracted members for a single Java type declaration.

    Args:
        class_name:       Simple name of the class, interface, or enum.
        package:          Package of the enclosing file.
        file_path:        Repository-relative path to the source file.
        repository:       Repository name.
        module:           Module label.
        declaration_type: Type of declaration ("class", "interface", or "enum").
        fields:           Extracted field declarations.
        methods:          Extracted method declarations.
        constructors:     Extracted constructor declarations.
        errors:           Non-fatal error messages collected during extraction.
    """

    class_name: str
    package: str
    file_path: str
    repository: str
    module: str
    declaration_type: str = "class"
    fields: list[JavaField] = field(default_factory=list)
    methods: list[JavaMethod] = field(default_factory=list)
    constructors: list[JavaConstructor] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "class": self.class_name,
            "package": self.package,
            "file_path": self.file_path,
            "repository": self.repository,
            "module": self.module,
            "fields": [f.to_dict() for f in self.fields],
            "methods": [m.to_dict() for m in self.methods],
            "constructors": [c.to_dict() for c in self.constructors],
            "errors": self.errors,
        }
