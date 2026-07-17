"""Domain models package — shared contracts exchanged between pipeline stages."""
from .context import PipelineContext
from .entity import Entity
from .extraction import ExtractionResult, ExtractionStatus
from .normalized import NormalizedDocument, NormalizedJson
from .relationship import Relationship
from .source import SourceMetadata, SourceType
from .api import API

__all__ = [
    "Entity",
    "Relationship",
    "SourceMetadata",
    "SourceType",
    "ExtractionResult",
    "ExtractionStatus",
    "NormalizedDocument",
    "NormalizedJson",
    "PipelineContext",
    "API",
]
