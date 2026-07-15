"""Build normalized entity dicts from OpenAPI metadata.

Re-exports entity builder functions from specialized modules.
Each builder module handles one entity type and stays under 150 LOC.
"""
from openapi_parser.endpoint_entity_builder import (
    build_endpoint_entity,
    build_parameter_entity,
)
from openapi_parser.schema_entity_builder import build_schema_entity
from openapi_parser.security_entity_builder import build_security_scheme_entity

__all__ = [
    "build_endpoint_entity",
    "build_parameter_entity",
    "build_schema_entity",
    "build_security_scheme_entity",
]


