"""Pipeline package exports."""
from pipeline.components import VersionTaggerComponent, derive_version_tag
from pipeline.converter import doc_to_entities
from pipeline.pipeline import SpacyExtractionPipeline, build_nlp
from pipeline.registry import apply_registered_components, register_component, registered_names
from pipeline.version_tagger import derive_version_with_source, derive_version_tag  # noqa: F811

__all__ = [
    "SpacyExtractionPipeline",
    "build_nlp",
    "register_component",
    "apply_registered_components",
    "registered_names",
    "VersionTaggerComponent",
    "derive_version_tag",
    "derive_version_with_source",
    "doc_to_entities",
]
