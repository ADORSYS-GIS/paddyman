"""Normalise annotation metadata into a consistent entity dict format.

Converts annotation data from the AST into ``{name, qualified_name, attributes}``
dicts suitable for storage in ``NormalizedJson.entities``.  FQN resolution uses
the import list extracted from the same source file.
"""
from __future__ import annotations

from typing import Any

from java_parser.java_ast.models import JavaAnnotation
from java_parser.annotation_string_parser import parse_attributes

AnnotationInput = JavaAnnotation | str


def _build_import_index(imports: list[str]) -> dict[str, str]:
    """Map simple class name → fully-qualified name from *imports*.

    Wildcard imports (``foo.bar.*``) are skipped — they cannot be resolved
    without a classpath.
    """
    index: dict[str, str] = {}
    for fqn in imports:
        if fqn.endswith(".*"):
            continue
        simple = fqn.rsplit(".", 1)[-1]
        index[simple] = fqn
    return index


def normalize_annotation_obj(ann: JavaAnnotation, imports: list[str]) -> dict[str, Any]:
    """Convert a :class:`~java_parser.java_ast.models.JavaAnnotation` to the
    normalised annotation dict.

    Args:
        ann:     Annotation from type-declaration AST.
        imports: Import list of the containing file for FQN resolution.

    Returns:
        ``{name, qualified_name, attributes}`` dict.
    """
    index = _build_import_index(imports)
    simple = ann.name.lstrip("@")
    return {
        "name": f"@{simple}",
        "qualified_name": index.get(simple, simple),
        "attributes": ann.attributes if ann.attributes else parse_attributes(ann.value),
    }


def normalize_annotation_str(
    raw: str, imports: list[str]
) -> dict[str, Any]:
    """Convert a plain annotation name string to the normalised dict.

    Args:
        raw:     Simple annotation name, with or without ``@`` prefix.
        imports: Import list of the containing file for FQN resolution.

    Returns:
        ``{name, qualified_name, attributes}`` dict.
    """
    index = _build_import_index(imports)
    body = raw.strip().lstrip("@")
    simple, has_args, args = body.partition("(")
    attributes = parse_attributes(args.rsplit(")", 1)[0]) if has_args else {}
    return {
        "name": f"@{simple}",
        "qualified_name": index.get(simple, simple),
        "attributes": attributes,
    }


def normalize_annotations_obj(
    annotations: list[JavaAnnotation], imports: list[str]
) -> list[dict[str, Any]]:
    """Normalise a list of :class:`JavaAnnotation` objects."""
    return [normalize_annotation_obj(a, imports) for a in annotations]


def normalize_annotation(annotation: AnnotationInput, imports: list[str]) -> dict[str, Any]:
    """Normalise one annotation object or legacy annotation string."""
    if isinstance(annotation, JavaAnnotation):
        return normalize_annotation_obj(annotation, imports)
    return normalize_annotation_str(annotation, imports)


def normalize_annotations(
    annotations: list[AnnotationInput], imports: list[str]
) -> list[dict[str, Any]]:
    """Normalise annotation objects or legacy annotation strings."""
    return [normalize_annotation(annotation, imports) for annotation in annotations]


def normalize_annotations_str(
    annotations: list[str], imports: list[str]
) -> list[dict[str, Any]]:
    """Normalise a list of plain annotation name strings."""
    return [normalize_annotation_str(a, imports) for a in annotations]
