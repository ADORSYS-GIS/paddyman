"""Domain models for extracted OpenAPI specification data (Chunks 3.1–3.4).

Chunk 3.1 — :class:`OpenApiMetadata`: top-level ``info`` block + server list.
Chunk 3.2 — :class:`EndpointMetadata`: individual path operation records.
Chunk 3.3 — :class:`PropertyMetadata`, :class:`SchemaMetadata`: component schema records.
Chunk 3.4 — :class:`RelationshipMetadata`: resolved ``$ref`` relationships.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OpenApiMetadata:
    """Structured metadata extracted from an OpenAPI YAML specification.

    Attributes:
        title:                API title from ``info.title``.
        version:              API version string from ``info.version``.
        spec_file:            Absolute path to the source specification file.
        openapi_version:      Value of the top-level ``openapi`` key (e.g. ``"3.0.1"``).
        description:          Optional full ``info.description`` text.
        description_summary:  Truncated description for display purposes.
        contact:              Optional ``info.contact`` mapping with name, email, url.
        license:              Optional ``info.license`` mapping with name, url.
        terms_of_service:     Optional ``info.termsOfService`` URL.
        external_docs:        Optional ``externalDocs`` mapping with url, description.
        servers:              List of server objects from the top-level ``servers`` key.
        extensions:           Custom extension fields (x-*) from info object.
    """

    title: str
    version: str
    spec_file: str
    openapi_version: str | None = None
    description: str | None = None
    description_summary: str | None = None
    contact: dict[str, Any] | None = None
    license: dict[str, Any] | None = None
    terms_of_service: str | None = None
    external_docs: dict[str, Any] | None = None
    servers: list[dict[str, Any]] = field(default_factory=list)
    extensions: dict[str, Any] | None = None


@dataclass
class EndpointMetadata:
    """Structured record for a single API path operation (Chunk 3.2).

    Attributes:
        type:         Fixed discriminator — always ``"endpoint"``.
        method:       HTTP method in upper-case (``GET``, ``POST``, …).
        path:         URL path template (e.g. ``/payments/{paymentId}``).
        api_title:    Title of the containing specification.
        spec_source:  File path or repository identifier of the source spec.
        operation_id: Optional ``operationId`` from the operation object.
        summary:      Optional one-line summary.
        description:  Optional extended description.
        tags:         List of tag strings applied to the operation.
        parameters:   List of structured parameter records (query, path, header, cookie).
        request_body: Raw ``requestBody`` mapping, or ``None`` when absent.
        responses:    Mapping of status-code strings to raw response objects.
    """

    type: str
    method: str
    path: str
    api_title: str
    spec_source: str
    operation_id: str | None = None
    summary: str | None = None
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    parameters: list["ParameterMetadata"] = field(default_factory=list)
    request_body: dict[str, Any] | None = None
    responses: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParameterMetadata:
    """Structured record for a single OpenAPI operation parameter.

    Covers query, path, header, and cookie parameters as defined in the
    OpenAPI 3.x specification. Used for both inline parameters in operations
    and reusable parameters from ``components.parameters``.

    Attributes:
        name:        Parameter name.
        location:    Where the parameter appears: ``query``, ``path``, ``header``,
                     or ``cookie`` (maps to the ``in`` field in the spec).
        required:    ``True`` when the parameter is mandatory.
        description: Optional description string.
        schema_type: JSON Schema primitive type of the parameter (e.g. ``string``).
        schema_ref:  ``$ref`` value when the parameter schema is a component reference.
        format:      Optional JSON Schema format hint (e.g. ``date``, ``uuid``).
        deprecated:  ``True`` when the parameter is marked deprecated.
        example:     Optional example value.
        enum_values: Enum values when the parameter is constrained to specific values.
        spec_source: File path or repository identifier (for reusable parameters).
    """

    name: str
    location: str  # query | path | header | cookie
    required: bool = False
    description: str | None = None
    schema_type: str | None = None
    schema_ref: str | None = None
    format: str | None = None
    deprecated: bool = False
    example: Any | None = None
    enum_values: list[Any] = field(default_factory=list)
    spec_source: str | None = None


@dataclass
class PropertyMetadata:
    """Metadata for a single property within an OpenAPI schema object (Chunk 3.3).

    Attributes:
        name:        Property key name.
        type:        JSON Schema primitive type (``string``, ``integer``, …) or ``None``.
        ref:         ``$ref`` value when the property type is a schema reference.
        description: Optional property description.
        required:    ``True`` when listed in the parent schema's ``required`` array.
        enum_values: Non-empty when the property itself carries an inline ``enum``.
        format:      Optional JSON Schema format hint (``date``, ``byte``, ``url``, …).
    """

    name: str
    type: str | None = None
    ref: str | None = None
    description: str | None = None
    required: bool = False
    enum_values: list[Any] = field(default_factory=list)
    format: str | None = None


@dataclass
class SchemaMetadata:
    """Structured record for a single schema definition (Chunk 3.3).

    Extracted from ``components.schemas`` in an OpenAPI document.

    Attributes:
        type:        Fixed discriminator — always ``"schema"``.
        name:        Schema key from ``components.schemas``.
        spec_source: File path or repository identifier of the source spec.
        schema_type: JSON Schema ``type`` value (``object``, ``string``, …).
        description: Optional schema description.
        properties:  Property records for object schemas.
        required:    List of required property names.
        enum_values: Enum values when the schema is an enumeration.
        refs:        ``$ref`` strings collected from ``allOf``/``oneOf``/``anyOf``.
        is_reference:      True if this schema is itself a $ref to another definition.
        ref_path:          Original $ref path if is_reference is True.
        external_refs:     List of external $ref paths.
        circular_refs:     List of $ref paths that form circular references.
        ref_dereferenced:  True if all refs have been successfully resolved.
    """

    type: str
    name: str
    spec_source: str
    schema_type: str | None = None
    description: str | None = None
    properties: list[PropertyMetadata] = field(default_factory=list)
    required: list[str] = field(default_factory=list)
    enum_values: list[Any] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)
    is_reference: bool = False
    ref_path: str | None = None
    external_refs: list[str] = field(default_factory=list)
    circular_refs: list[str] = field(default_factory=list)
    ref_dereferenced: bool = True


@dataclass
class RelationshipMetadata:
    """A directed relationship produced by resolving OpenAPI ``$ref`` values (Chunk 3.4).

    Three relationship kinds are generated:

    * ``RETURNS``    — an endpoint returns a schema (via response ``$ref``).
    * ``ACCEPTS``    — an endpoint accepts a schema (via requestBody ``$ref``).
    * ``REFERENCES`` — a schema references another schema (via allOf/oneOf/anyOf
      or property ``$ref``).

    Attributes:
        type:             Fixed discriminator — always ``"relationship"``.
        source:           Relationship source label, e.g. ``"POST /payments"`` or
                          a schema name.
        target:           Target schema name.
        relationship:     One of ``RETURNS``, ``ACCEPTS``, ``REFERENCES``.
        spec_source:      File path or repository identifier of the source spec.
        endpoint_method:  HTTP method when source is an endpoint, else ``None``.
        endpoint_path:    URL path when source is an endpoint, else ``None``.
        ref_path:         The original ``$ref`` string that produced this record.
    """

    type: str
    source: str
    target: str
    relationship: str
    spec_source: str
    endpoint_method: str | None = None
    endpoint_path: str | None = None
    ref_path: str | None = None


@dataclass
class RequestBodyMetadata:
    """Structured record for a single ``components.requestBodies`` entry.

    Represents a reusable request body definition that can be referenced by
    multiple operations via ``$ref``.

    Attributes:
        name:          Request body key from ``components.requestBodies``.
        spec_source:   File path or repository identifier of the source spec.
        required:      ``True`` when the request body is mandatory for the operation.
        description:   Optional description of the request body.
        content_types: List of media types supported (e.g. ``application/json``).
        schema_ref:    ``$ref`` value when the content schema is a component reference.
        schema_type:   JSON Schema type when the schema is defined inline.
    """

    name: str
    spec_source: str
    required: bool = False
    description: str | None = None
    content_types: list[str] = field(default_factory=list)
    schema_ref: str | None = None
    schema_type: str | None = None


@dataclass
class ResponseMetadata:
    """Structured record for a single ``components.responses`` entry.

    Represents a reusable response definition that can be referenced by
    multiple operations via ``$ref``.

    Attributes:
        name:          Response key from ``components.responses``.
        spec_source:   File path or repository identifier of the source spec.
        http_status:   HTTP status code this response represents (e.g. ``"201"``).
        description:   Required description of the response.
        content_types: List of media types in the response (e.g. ``application/json``).
        schema_ref:    ``$ref`` value when the response schema is a component reference.
        schema_type:   JSON Schema type when the schema is defined inline.
        headers:       Response header definitions.
    """

    name: str
    spec_source: str
    description: str
    http_status: str | None = None
    content_types: list[str] = field(default_factory=list)
    schema_ref: str | None = None
    schema_type: str | None = None
    headers: dict[str, Any] = field(default_factory=dict)


@dataclass
class SecuritySchemeMetadata:
    """Structured record for a single ``components.securitySchemes`` entry.

    Covers HTTP bearer/basic, API key, OAuth2, and OpenID Connect schemes
    as defined in the OpenAPI 3.x specification.

    Attributes:
        name:            Security scheme key from ``components.securitySchemes``.
        type:            Scheme type: ``http``, ``apiKey``, ``oauth2``,
                         or ``openIdConnect``.
        spec_source:     File path or repository identifier of the source spec.
        scheme:          HTTP authentication scheme (e.g. ``bearer``, ``basic``).
                         Only relevant when ``type`` is ``http``.
        bearer_format:   Hint for bearer token format (e.g. ``JWT``).
        in_:             Location of the API key: ``header``, ``query``, or ``cookie``.
                         Only relevant when ``type`` is ``apiKey``.
        parameter_name:  Name of the API key parameter.  Only relevant when
                         ``type`` is ``apiKey``.
        open_id_connect_url: Discovery URL.  Only relevant when ``type`` is
                             ``openIdConnect``.
        description:     Optional description of the security scheme.
        flows:           OAuth2 flow definitions keyed by flow type
                         (``implicit``, ``password``, ``clientCredentials``,
                         ``authorizationCode``).  Empty when ``type`` is not
                         ``oauth2``.
    """

    name: str
    type: str
    spec_source: str
    scheme: str | None = None
    bearer_format: str | None = None
    in_: str | None = None
    parameter_name: str | None = None
    open_id_connect_url: str | None = None
    description: str | None = None
    flows: dict[str, Any] = field(default_factory=dict)
