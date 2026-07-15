"""OpenAPI $ref dereferencer — resolve internal refs before entity extraction.

Resolves internal `$ref` pointers. External refs are marked with metadata.
Circular references are detected and tracked.
"""
from __future__ import annotations

import logging
from typing import Any

from openapi_parser.ref_metadata import RefMetadata
from openapi_parser.ref_utils import is_external_ref, is_internal_ref

logger = logging.getLogger(__name__)

_MAX_DEPTH = 200


class InternalRefResolver:
    """Resolve internal OpenAPI $ref pointers and track resolution metadata."""

    def __init__(self, spec: dict[str, Any], max_depth: int = _MAX_DEPTH) -> None:
        """Initialize resolver.
        
        Args:
            spec: Parsed OpenAPI YAML document.
            max_depth: Maximum recursion depth for nested refs.
        """
        self.spec = spec
        self.max_depth = max_depth
        self.ref_metadata_cache: dict[str, RefMetadata] = {}

    def resolve(self, obj: Any, visited: frozenset[str] | None = None, depth: int = 0) -> Any:
        """Recursively resolve $ref pointers in the given object.
        
        Args:
            obj: The object to resolve (dict, list, or primitive).
            visited: Set of ref paths already visited.
            depth: Current recursion depth.
            
        Returns:
            Resolved object with internal refs replaced by their targets.
        """
        visited = visited or frozenset()
        
        if depth > self.max_depth:
            logger.warning("Max depth %d exceeded during ref resolution", self.max_depth)
            return obj
        
        if isinstance(obj, dict):
            ref_value = obj.get("$ref")
            if isinstance(ref_value, str):
                return self._resolve_ref(ref_value, visited, depth)
            return {k: self.resolve(v, visited, depth) for k, v in obj.items()}
        
        if isinstance(obj, list):
            return [self.resolve(item, visited, depth) for item in obj]
        
        return obj

    def _resolve_ref(self, ref: str, visited: frozenset[str], depth: int) -> Any:
        """Resolve a single $ref value and track metadata."""
        if ref in visited:
            logger.debug("Circular ref detected: %s", ref)
            self._track_ref(ref, dereferenced=False, circular=True)
            return {"$ref": ref, "ref_cycle_detected": True}
        
        if is_external_ref(ref):
            self._track_ref(ref, dereferenced=False, is_external=True)
            return {"$ref": ref, "ref_type": "external"}
        
        if is_internal_ref(ref):
            target = self._follow_internal_ref(ref)
            
            if target is None:
                logger.warning("Broken internal ref: %s", ref)
                self._track_ref(ref, dereferenced=False)
                return {"$ref": ref, "ref_resolved": False}
            
            self._track_ref(ref, dereferenced=True)
            new_visited = visited | {ref}
            return self.resolve(target, new_visited, depth + 1)
        
        logger.warning("Unknown ref format: %s", ref)
        self._track_ref(ref, dereferenced=False)
        return {"$ref": ref, "ref_resolved": False}

    def _track_ref(
        self, ref: str, dereferenced: bool, is_external: bool = False, circular: bool = False
    ) -> None:
        """Track metadata for a resolved $ref."""
        if ref not in self.ref_metadata_cache:
            self.ref_metadata_cache[ref] = RefMetadata(
                ref_path=ref, dereferenced=dereferenced, is_external=is_external, circular=circular
            )

    def get_ref_metadata(self, ref: str) -> RefMetadata | None:
        """Get tracked metadata for a $ref."""
        return self.ref_metadata_cache.get(ref)

    def _follow_internal_ref(self, ref: str) -> Any:
        """Follow an internal JSON Pointer to its target."""
        if not ref.startswith("#/"):
            return None
        
        parts = ref[2:].split("/")
        obj: Any = self.spec
        
        for part in parts:
            if not isinstance(obj, dict) or part not in obj:
                return None
            obj = obj[part]
        
        return obj


def dereference_spec(spec: dict[str, Any], max_depth: int = _MAX_DEPTH) -> dict[str, Any]:
    """Convenience function to dereference all refs in an OpenAPI spec."""
    resolver = InternalRefResolver(spec, max_depth)
    return resolver.resolve(spec)

