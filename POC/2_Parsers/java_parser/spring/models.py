"""Domain models for Spring annotation extraction.

Carries structured metadata about Spring-annotated Java classes, compatible
with downstream extraction and graph normalisation stages.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── Classification constants ───────────────────────────────────────────────────

SPRING_ANNOTATION_NAMES: frozenset[str] = frozenset(
    {
        "RestController",
        "Controller",
        "RequestMapping",
        "GetMapping",
        "PostMapping",
        "PutMapping",
        "DeleteMapping",
        "PatchMapping",
        "Service",
        "Repository",
        "Component",
        "Entity",
    }
)

CONTROLLER_ANNOTATIONS: frozenset[str] = frozenset(
    {
        "RestController",
        "Controller",
        "RequestMapping",
        "GetMapping",
        "PostMapping",
        "PutMapping",
        "DeleteMapping",
        "PatchMapping",
    }
)

SERVICE_ANNOTATIONS: frozenset[str] = frozenset({"Service"})
REPOSITORY_ANNOTATIONS: frozenset[str] = frozenset({"Repository"})
COMPONENT_ANNOTATIONS: frozenset[str] = frozenset({"Component"})
ENTITY_ANNOTATIONS: frozenset[str] = frozenset({"Entity"})

HTTP_METHOD_MAP: dict[str, str] = {
    "GetMapping": "GET",
    "PostMapping": "POST",
    "PutMapping": "PUT",
    "DeleteMapping": "DELETE",
    "PatchMapping": "PATCH",
}

# Priority-ordered component type resolution
_COMPONENT_PRIORITY: list[tuple[frozenset[str], str]] = [
    (CONTROLLER_ANNOTATIONS, "controller"),
    (SERVICE_ANNOTATIONS, "service"),
    (REPOSITORY_ANNOTATIONS, "repository"),
    (ENTITY_ANNOTATIONS, "entity"),
    (COMPONENT_ANNOTATIONS, "component"),
]


# ── Data models ────────────────────────────────────────────────────────────────


@dataclass
class SpringAnnotation:
    """A single Spring annotation with its extracted arguments.

    Args:
        name:       Annotation simple name (e.g. ``"RequestMapping"``).
        value:      Primary (unnamed) annotation value, if present.
        attributes: Named element–value pairs (e.g. ``{"method": "GET"}``).
    """

    name: str
    value: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"name": self.name}
        if self.value is not None:
            d["value"] = self.value
        if self.attributes:
            d["attributes"] = self.attributes
        return d


@dataclass
class SpringComponentResult:
    """Structured Spring component metadata extracted from one class declaration.

    Args:
        component_type:      Classified type: controller / service / repository
                             / entity / component.
        class_name:          Simple (unqualified) class name.
        annotations:         Ordered list of Spring annotation names present.
        annotation_details:  Full annotation objects with values and attributes.
        package:             Java package of the class.
        file_path:           Repository-relative source file path.
        repository:          Repository name (for provenance).
        module:              Module label (for provenance).
        mapped_paths:        URL path values extracted from mapping annotations.
        http_methods:        HTTP verbs inferred from mapping annotations.
    """

    component_type: str
    class_name: str
    annotations: list[str]
    annotation_details: list[SpringAnnotation]
    package: str
    file_path: str
    repository: str
    module: str
    mapped_paths: list[str] = field(default_factory=list)
    http_methods: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict suitable for JSON output."""
        return {
            "type": self.component_type,
            "class": self.class_name,
            "annotations": self.annotations,
            "annotation_details": [a.to_dict() for a in self.annotation_details],
            "mapped_paths": self.mapped_paths,
            "http_methods": self.http_methods,
            "package": self.package,
            "file_path": self.file_path,
            "repository": self.repository,
            "module": self.module,
        }


def resolve_component_type(annotation_names: list[str]) -> str | None:
    """Return the highest-priority Spring component type for *annotation_names*.

    Returns ``None`` when no recognised Spring stereotype annotation is found.
    """
    name_set = frozenset(annotation_names)
    for candidates, label in _COMPONENT_PRIORITY:
        if name_set & candidates:
            return label
    return None
