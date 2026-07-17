"""SourcePatternRule — source-specific name extraction before casing normalisation.

Applies parser-specific transformations so that role-bearing suffixes and
protocol-specific prefixes are removed before :class:`~rules.casing.CasingRule`
converts the result to PascalCase.

Supported transformations:
- **Java parsers** — strip class-role suffixes (``Controller``, ``Service``, …).
- **OpenAPI parsers** — extract the resource name from ``"METHOD /path"``
  or bare ``"/path"`` strings.
- **Other parsers** — return ``None`` (pass-through; no transformation).
"""
from __future__ import annotations

import re

# Ordered from longest to shortest to prevent partial matches
# (e.g. "ServiceImpl" stripped before "Service" would corrupt the name).
_JAVA_SUFFIXES: tuple[str, ...] = (
    "ServiceImpl",
    "RepositoryImpl",
    "RestController",
    "Controller",
    "Service",
    "Repository",
    "Impl",
    "Facade",
    "Adapter",
    "Factory",
    "Handler",
    "Provider",
    "Manager",
)

_JAVA_PARSERS: frozenset[str] = frozenset(
    {"java_parser", "java", "spring_parser"}
)
_OPENAPI_PARSERS: frozenset[str] = frozenset(
    {"openapi_parser", "openapi", "yaml_parser"}
)

_HTTP_PREFIX = re.compile(
    r"^(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+", re.IGNORECASE
)
_PATH_PARAM = re.compile(r"\{[^}]+\}")

# Words that should not be singularized (would produce wrong result)
_NO_SINGULARIZE: frozenset[str] = frozenset(
    {"access", "address", "process", "status", "class", "alias", "basis"}
)


def _strip_java_suffix(name: str) -> str:
    """Strip one known role suffix from *name* if present."""
    for suffix in _JAVA_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[: -len(suffix)]
    return name


def _singularize(word: str) -> str:
    """Conservative REST-resource singularization."""
    lower = word.lower()
    if lower in _NO_SINGULARIZE:
        return word
    if lower.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"      # "capabilities" → "capability"
    if lower.endswith("ses") and len(word) > 4:
        return word[:-2]            # "statuses" → "status"
    if lower.endswith("s") and len(word) > 3 and not lower.endswith("ss"):
        return word[:-1]            # "payments" → "payment"
    return word


def _openapi_path_to_resource(name: str) -> str:
    """Extract a resource noun from an OpenAPI path expression."""
    # Remove "POST " / "GET " style prefix
    path = _HTTP_PREFIX.sub("", name).strip()
    # Remove path parameters: "{paymentId}" → ""
    path = _PATH_PARAM.sub("", path)
    # Take the last non-empty path segment
    segments = [s.strip() for s in path.split("/") if s.strip()]
    if not segments:
        return name
    return _singularize(segments[-1])


class SourcePatternRule:
    """Apply source-specific name extraction before casing normalisation."""

    def apply(
        self,
        name: str,
        entity_type: str,
        source_parser: str,
    ) -> str | None:
        """Transform *name* based on *source_parser* conventions.

        Returns ``None`` when no transformation is needed (pass-through).
        """
        _ = entity_type
        if not name or not name.strip():
            return None

        if source_parser in _JAVA_PARSERS:
            stripped = _strip_java_suffix(name.strip())
            return stripped if stripped != name else None

        if source_parser in _OPENAPI_PARSERS:
            if "/" in name or _HTTP_PREFIX.match(name):
                resource = _openapi_path_to_resource(name)
                return resource if resource != name else None

        return None
