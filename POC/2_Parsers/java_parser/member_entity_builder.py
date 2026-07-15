"""Build NormalizedJson entity dicts from Java class member declarations.

Converts :class:`~java_parser.members.models.JavaMethod` and
:class:`~java_parser.members.models.JavaConstructor` objects into the flat
``dict`` format stored in ``NormalizedJson.entities``.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from java_parser.members.models import JavaConstructor, JavaMethod

_VISIBILITY_MODIFIERS = frozenset({"public", "protected", "private"})


def _visibility(modifiers: list[str]) -> str:
    for mod in modifiers:
        if mod in _VISIBILITY_MODIFIERS:
            return mod
    return "package-private"


def method_to_entity(
    method: JavaMethod, 
    document_id: str, 
    imports: list[str] | None = None,
    is_interface: bool = False,
) -> dict[str, Any]:
    """Convert a :class:`JavaMethod` to an entity dict.

    Args:
        method:       Extracted method declaration.
        document_id:  Document ID of the containing file.
        imports:      Import list for annotation resolution.
        is_interface: True if the method belongs to an interface.

    Returns:
        Entity dict conforming to the ``NormalizedJson.entities`` schema.
        Note: Parameters are extracted separately via parameter_entity_builder.
    """
    qualified_class = (
        f"{method.package}.{method.class_name}" if method.package else method.class_name
    )
    is_abstract = "abstract" in method.modifiers
    start_line = method.location.start_line + 1
    end_line = method.location.end_line + 1
    
    # Determine if method has a body (concrete implementation)
    has_body = not (is_interface or is_abstract) or (start_line != end_line)
    line_count = end_line - start_line + 1
    
    return {
        "type": "Method",
        "name": method.name,
        "class": method.class_name,
        "qualified_class": qualified_class,
        "visibility": _visibility(method.modifiers),
        "return_type": method.return_type,
        "parameter_count": len(method.parameters),
        "annotation_count": len(method.annotations),
        "uuid": str(uuid4()),
        "is_static": "static" in method.modifiers,
        "is_abstract": is_abstract,
        "has_body": has_body,
        "is_interface_method": is_interface,
        "line_count": line_count,
        "start_line": start_line,
        "end_line": end_line,
        "source": document_id,
        "repository": method.repository,
        "module": method.module,
        "file_path": method.file_path,
    }


def constructor_to_entity(
    ctor: JavaConstructor, document_id: str, imports: list[str] | None = None
) -> dict[str, Any]:
    """Convert a :class:`JavaConstructor` to an entity dict.

    Args:
        ctor:        Extracted constructor declaration.
        document_id: Document ID of the containing file.

    Returns:
        Entity dict with ``type = "Constructor"`` and ``return_type = null``.
        Note: Parameters are extracted separately via parameter_entity_builder.
    """
    qualified_class = (
        f"{ctor.package}.{ctor.class_name}" if ctor.package else ctor.class_name
    )
    return {
        "type": "Constructor",
        "name": ctor.name,
        "class": ctor.class_name,
        "qualified_class": qualified_class,
        "visibility": _visibility(ctor.modifiers),
        "return_type": None,
        "parameter_count": len(ctor.parameters),
        "annotation_count": len(ctor.annotations),
        "uuid": str(uuid4()),
        "is_static": False,
        "is_abstract": False,
        "start_line": ctor.location.start_line + 1,
        "end_line": ctor.location.end_line + 1,
        "source": document_id,
        "repository": ctor.repository,
        "module": ctor.module,
        "file_path": ctor.file_path,
    }


