"""Spring annotation extraction sub-package.

Public API for extracting Spring Framework annotations from parsed Java ASTs.
"""
from .classifier import extract_spring_components
from .models import SpringAnnotation, SpringComponentResult

__all__ = [
    "SpringAnnotation",
    "SpringComponentResult",
    "extract_spring_components",
]
