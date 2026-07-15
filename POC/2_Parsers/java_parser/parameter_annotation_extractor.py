"""Extract annotation entities from Java parameter declarations."""
from __future__ import annotations

from typing import Any

from java_parser.annotation_entity_builder import extract_annotation_entities
from java_parser.members.models import JavaParameter


def extract_parameter_annotation_entities(
    parameters: list[JavaParameter],
    method_name: str,
    file_path: str,
    repository: str,
    module: str,
    start_line: int,
    document_id: str,
    imports: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Extract Annotation entities for all parameters.

    Args:
        parameters:  List of JavaParameter objects.
        method_name: Name of the owning method/constructor.
        file_path:   Repository-relative file path.
        repository:  Repository name.
        module:      Module label.
        start_line:  Line number where parameters are defined.
        document_id: Document ID of the containing file.
        imports:     Import list for FQN annotation resolution.

    Returns:
        List of Annotation entity dicts for all parameters.
    """
    annotation_entities: list[dict[str, Any]] = []
    
    for param in parameters:
        param_annotations = extract_annotation_entities(
            param.annotations,
            target_type="Parameter",
            target_name=f"{method_name}.{param.name}",
            file_path=file_path,
            repository=repository,
            module=module,
            start_line=start_line,
            document_id=document_id,
            imports=imports,
        )
        annotation_entities.extend(param_annotations)
    
    return annotation_entities
