"""Build normalized entity dicts from OpenAPI metadata.

Re-exports entity builder functions from specialized modules.
Each builder module handles one entity type and stays under 150 LOC.
"""
from openapi_parser.endpoint_entity_builder import (
    build_endpoint_entity,
    build_parameter_entity,
)
from openapi_parser.operation_entity_builder import build_operation_entity, build_tag_entity
from openapi_parser.request_body_entity_builder import build_request_body_entity
from openapi_parser.response_entity_builder import build_response_entity
from openapi_parser.schema_entity_builder import build_schema_entities, build_schema_entity
from openapi_parser.api_entity_builder import build_api_entity
from openapi_parser.security_entity_builder import build_security_scheme_entity

__all__ = [
    "build_api_entity",
    "build_endpoint_entity",
    "build_parameter_entity",
    "build_operation_entity",
    "build_tag_entity",
    "build_request_body_entity",
    "build_response_entity",
    "build_schema_entities",
    "build_schema_entity",
    "build_security_scheme_entity",
]


