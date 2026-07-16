# OpenAPI Parser

Parses OpenAPI 3.x YAML specifications into structured domain models for downstream graph ingestion.

## Pipeline Stages

| Stage | Module | Output |
|-------|--------|--------|
| 0. $ref dereferencing | `ref_dereferencer.py` | Resolved spec with internal refs replaced |
| 1. YAML loading | `loader.py` + `info_extractor.py` | `OpenApiMetadata` — comprehensive info block metadata |
| 2. Endpoint extraction | `extractor.py` | `EndpointMetadata` — method, path, operation details |
| 3. Schema extraction | `schema_extractor.py` | `SchemaMetadata` — components.schemas, properties |
| 4. Reference resolution | `ref_resolver.py` | `RelationshipMetadata` — RETURNS / ACCEPTS / REFERENCES |
| 5. Security scheme extraction | `security_extractor.py` | `SecuritySchemeMetadata` — security definitions |
| 6. Request body extraction | `request_body_extractor.py` | `RequestBody` entities from inline operations + components.requestBodies |
| 7. Response extraction | `response_extractor.py` | `Response` entities from inline operations + components.responses |
| 8. Operation extraction | `operation_extractor.py` | `Operation` and `Tag` entities from path operations |
| 9. Entity building | `entity_builder.py` | Entity dictionaries with UUIDs (including one `API` entity per spec) |
| 10. Relationship building | `relationship_builder.py` + `operation_relationships.py` | Relationship dictionaries linking entities (including HAS_REQUEST_BODY / HAS_RESPONSE / USES_SCHEMA / HAS_PROPERTY / HAS_ENUM_VALUE / IMPLEMENTS_OPERATION / TAGGED_AS / REQUIRES_SECURITY / REQUIRES_SCOPE / DEFINES / COMPOSES_ALL_OF / ONE_OF / ANY_OF / NOT) |
| 11. Orchestration | `main.py` | Summary dict |

## API Info Metadata Extraction

The `info_extractor.py` module extracts comprehensive API-level metadata from the OpenAPI `info` object and related top-level fields.

### Extracted Fields

| Field | Description | Required |
|-------|-------------|----------|
| `title` | API title from `info.title` | Yes |
| `version` | API version from `info.version` | Yes |
| `description` | Full API description text | No |
| `description_summary` | Truncated description (200 chars) for display | No |
| `terms_of_service` | Terms of service URL from `info.termsOfService` | No |
| `contact` | Contact information mapping (name, email, url) | No |
| `license` | License information mapping (name, url) | No |
| `external_docs` | External documentation mapping (url, description) | No |
| `openapi_version` | OpenAPI spec version (`3.0.1`, `2.0`, etc.) | No |
| `servers` | List of server objects from top-level `servers` | No |
| `extensions` | Custom extension fields (`x-*`) from info object | No |

### Example Output

```python
{
    "title": "NextGenPSD2 XS2A Framework",
    "version": "1.3.16_2025-11-27",
    "description": "Comprehensive framework for payment services...",
    "description_summary": "Comprehensive framework for payment services supporting multiple account types...",
    "terms_of_service": "https://example.com/terms",
    "contact": {
        "name": "Berlin Group",
        "email": "support@berlin-group.org",
        "url": "https://www.berlin-group.org"
    },
    "license": {
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html"
    },
    "external_docs": {
        "url": "https://docs.example.com",
        "description": "Additional documentation"
    },
    "openapi_version": "3.0.1",
    "servers": [
        {
            "url": "https://api.example.com/v1",
            "description": "Production"
        }
    ],
    "extensions": {
        "x-api-id": "psd2-001",
        "x-audience": "public"
    }
}
```

### Module Structure

- **`info_extractor.py`**: Metadata extraction logic (< 150 LOC)
- **`loader.py`**: YAML file discovery and loading (< 150 LOC)
- Both modules are independently testable and maintain strict separation of concerns

## $ref Dereferencing

Before entity extraction, all internal `$ref` pointers (matching `#/components/...`) are resolved
to their target nodes. This eliminates raw `$ref` strings from structured entities, simplifying
downstream graph construction.

**Internal refs** (`#/components/parameters/X`):
- Resolved recursively up to max depth (default: 5)
- Replaced with the target object inline
- No `$ref` key remains in the output

**External refs** (`https://...` or relative file paths like `../common.yaml#/X`):
- Preserved as-is with metadata: `{"$ref": "...", "ref_type": "external"}`
- Not resolved (target file may not be available)

**Broken refs** (non-existent internal targets):
- Marked with `{"$ref": "...", "ref_resolved": false}`
- No exception raised; processing continues

**Circular refs** (A → B → A):
- Detected and broken with `{"$ref": "...", "ref_cycle_detected": true}`
- No infinite loop; recursion terminates at cycle detection

Module: `openapi_parser.ref_dereferencer`

Example:
```python
from openapi_parser.ref_dereferencer import dereference_spec

dereferenced_spec = dereference_spec(raw_spec, max_depth=5)
```

## Input

OpenAPI 3.x `.yaml` or `.yml` files.  The default root directory is
`settings.yaml_spec_dir` (env: `YAML_SPEC_DIR`, default `/opt/airflow/DataSource/yaml_spec`).

## Running

Normal pipeline execution uses the single parser runner:

```bash
cd POC
PYTHONPATH=.:2_Parsers python3 2_Parsers/parser_pipeline.py
```

This runs Java, OpenAPI, and Markdown parsing and writes `java_openapi_markdown_parser_output.json`.
Running this parser directly writes one JSON file per YAML/YML spec under `openapi_specs/`.
Use `openapi_parser.main` only for isolated parser tests or debugging.

### As a module (recommended)
```bash
cd POC
.venv/bin/python -m openapi_parser.main
```

### With an explicit directory
```python
from openapi_parser.main import run_pipeline

summary = run_pipeline("/path/to/yaml_specs")
```

### As a script
```bash
cd POC/2_Parsers
python openapi_parser/main.py
```

## Output

`run_pipeline()` returns a summary dictionary:

```json
{
  "specs_loaded":        3,
  "apis_discovered":     2,
  "endpoints_extracted": 41,
  "schemas_extracted":   18,
  "dtos_extracted":      12,
  "enums_extracted":      6,
  "refs_resolved":       27,
  "endpoint_schema_rels":19,
  "security_schemes_extracted": 5,
  "request_bodies_extracted": 8,
  "responses_extracted": 15,
  "chunks_produced":     127,
  "errors":              []
}
```

| Key | Description |
|-----|-------------|
| `specs_loaded` | Number of valid YAML files parsed |
| `apis_discovered` | Unique API titles (`info.title`) |
| `endpoints_extracted` | Total HTTP operations across all specs |
| `schemas_extracted` | Total `components.schemas` entries |
| `dtos_extracted` | Schemas with `type: object` and non-empty `properties` |
| `enums_extracted` | Schemas with `enum` values |
| `refs_resolved` | Total `$ref` relationships resolved |
| `endpoint_schema_rels` | RETURNS + ACCEPTS relationships |
| `security_schemes_extracted` | Total security scheme definitions |
| `request_bodies_extracted` | Total reusable request body definitions |
| `responses_extracted` | Total reusable response definitions |
| `chunks_produced` | Total semantic chunks from splitting stage |
| `errors` | Per-spec error messages (pipeline continues on failure) |

## RequestBody Entities

Request bodies are emitted as first-class `RequestBody` entities and are no longer embedded inside `Endpoint` entities.

- Sources covered:
  - Inline `requestBody` definitions under `paths.{path}.{method}`
  - Shared definitions under `components.requestBodies`
- Deduplication:
  - Reused request bodies are deduplicated by stable content fingerprint
  - Reuse is tracked via `properties.reusable`
- Captured metadata:
  - `description`
  - `required`
  - `content_types`
  - `source_file`
  - `ref_path` (when component-based)

### RequestBody Relationships

- `HAS_REQUEST_BODY`
  - `Endpoint -> RequestBody`
  - Properties: `endpoint_path`, `endpoint_method`, `required`
- `USES_SCHEMA`
  - `RequestBody -> Schema/DTO/Enum`
  - Properties: `content_type`, `schema_name`

## API Entity

One `API` entity is produced for each parsed specification file, capturing the full `info` block as a queryable node in the knowledge graph.

```json
{
  "type": "API",
  "name": "NextGenPSD2 XS2A Framework",
  "id": "uuid-string",
  "source_file": "/path/to/spec.yaml",
  "title": "NextGenPSD2 XS2A Framework",
  "version": "1.3.16_2025-11-27",
  "description": "The NextGenPSD2 Framework offers...",
  "contact_name": "Berlin Group",
  "contact_email": "support@berlin-group.org",
  "contact_url": "https://www.berlin-group.org",
  "license_name": "Apache 2.0",
  "license_url": "https://www.apache.org/licenses/LICENSE-2.0.html",
  "terms_of_service": "https://example.com/terms",
  "openapi_version": "3.0.1"
}
```

**API entity notes:**

- One entity per specification file — multiple specs produce multiple API entities
- All optional fields are `null` when absent
- `DEFINES` relationships link the API entity to every endpoint, schema, DTO, enum, security scheme, request body, response, parameter, and operation extracted from that spec
- The entity enables querying: which endpoints belong to an API, which schemas does an API define, what versions exist

**Module:** `openapi_parser.api_entity_builder`

## DTO And Enum Entities

Schema entities are classified at entity-build time:

- `Enum`: any schema with non-empty `enum`
- `DTO`: schema with `type: object` and non-empty `properties`
- `Schema`: all other schemas (simple primitives, composition-only schemas)

Captured DTO metadata:

- `properties.required_fields`
- `properties.property_count`
- `properties.source_file`

Captured Enum metadata:

- `properties.values`
- `properties.value_count`
- `properties.base_type`

### DTO/Enum Relationships

- `HAS_PROPERTY`
  - `DTO -> Schema` (one generated property schema per DTO field)
  - Properties: `property_name`, `required`, `nullable`
- `HAS_ENUM_VALUE`
  - `Enum -> EnumValue`
  - Properties: `value`, `position`

## Response Entities

Responses are emitted as first-class `Response` entities and are no longer embedded inside `Endpoint` entities.

- Sources covered:
  - Inline `responses` under `paths.{path}.{method}`
  - Shared definitions under `components.responses`
- Captured metadata:
  - `status_code`
  - `description`
  - `content_types`
  - `source_file`
  - `reusable`
  - `ref_path` (when component-based)
  - `is_error` and `error_category`
- Status categorization:
  - `2xx`: `success`
  - `4xx`: `client_error`
  - `5xx`: `server_error`

### Response Relationships

- `HAS_RESPONSE`
  - `Endpoint -> Response`
  - Properties: `endpoint_path`, `endpoint_method`, `status_code`
- `USES_SCHEMA`
  - `Response -> Schema/DTO/Enum`
  - Properties: `content_type`, `schema_name`

## Operation And Tag Entities

Operations are emitted as first-class `Operation` entities and endpoint tags are normalized into separate `Tag` entities.

- Sources covered:
  - Path operations under `paths.{path}.{method}`
- Captured `Operation` metadata:
  - `operation_id` (placeholder generated when missing)
  - `summary`
  - `description`
  - `tags`
  - `deprecated`
  - `external_docs`
  - `method`, `path`, `source_file`
- Captured `Tag` metadata:
  - `tag_name`
  - `source_file`

### Operation Relationships

- `IMPLEMENTS_OPERATION`
  - `Endpoint -> Operation`
  - Properties: `method`, `path`
- `TAGGED_AS`
  - `Operation -> Tag`
  - Properties: `tag_name`

## Tests

```bash
cd POC
.venv/bin/pytest 2_Parsers/openapi_parser/tests/ -v
```

## Module Structure

```
openapi_parser/
  __init__.py                         package marker
  models.py                           domain model dataclasses (all stages)
  loader.py                           YAML discovery + metadata extraction
  extractor.py                        endpoint extraction from paths object
  entity_builder.py                   convert EndpointMetadata and SchemaMetadata to entity dicts
  request_body_entity_builder.py      convert requestBody objects to RequestBody entities
  dto_entity_builder.py               convert object schemas to DTO + property Schema entities
  enum_entity_builder.py              convert enum schemas to Enum + EnumValue entities
  dto_enum_relationships.py           DTO/Enum relationship extraction helpers
  request_body_extractor.py           extract request bodies from paths + components
  request_body_relationships.py       RequestBody relationship extraction helpers
  response_entity_builder.py          convert response objects to Response entities
  response_extractor.py               extract responses from paths + components
  response_relationships.py           Response relationship extraction helpers
  operation_entity_builder.py         convert operation objects to Operation and Tag entities
  operation_extractor.py              extract operations and tags from paths
  operation_relationships.py          Operation/Tag relationship extraction helpers
  api_entity_builder.py               build one API entity per spec from the info block
  api_relationship_builder.py         DEFINES relationships from API entity to owned entities
  security_requirement_extractor.py   effective security extraction (global/path/operation)
  security_relationship_builder.py    REQUIRES_SECURITY and REQUIRES_SCOPE relationship helpers
  request_response_entity_builder.py  convert RequestBodyMetadata and ResponseMetadata to entity dicts
  relationship_builder.py             build relationships between entities
  relationship_extractors.py          relationship extraction functions
  readers.py                          LlamaIndex document readers (local + GitLab)
  schema_extractor.py                 schema extraction from components.schemas
  parameter_extractor.py              parameter extraction from components.parameters
  security_extractor.py               security scheme extraction from components.securitySchemes
  request_response_extractor.py       request body and response extraction from components
  ref_dereferencer.py                 $ref dereferencing (internal refs → inline objects)
  ref_resolver.py                     $ref resolution → relationship records
  main.py                             pipeline orchestrator (this entrypoint)
  tests/
    test_loader.py
    test_extractor.py
    test_entity_builder.py
    test_readers.py
    test_schema_extractor.py
    test_parameter_extractor.py
    test_request_response_extractor.py
    test_request_response_entity_builder.py
    test_ref_dereferencer.py
    test_ref_resolver.py
    test_relationship_builder.py
    test_main.py
```

## Document Metadata

Each `NormalizedDocument` includes enriched `source_metadata` with OpenAPI-specific fields extracted from the `info` block and top-level spec properties:

```json
{
  "file_path": "/path/to/spec.yaml",
  "relative_path": "openfinance/.../spec.yaml",
  "source_parser": "openapi_parser",
  "api_title": "NextGenPSD2 XS2A Framework",
  "api_version": "1.3.16_2025-11-27",
  "api_description_summary": "The NextGenPSD2 Framework Version 1.3.14 offers a modern, open, harmonised and interoperable set of Application Programming Interfaces (APIs) as the safest and most efficient...",
  "servers": [
    {
      "url": "https://api.example.com/v1",
      "description": "Production server"
    }
  ]
}
```

### Metadata Fields

| Field | Description |
|-------|-------------|
| `file_path` | Absolute path to the source YAML file |
| `relative_path` | Path relative to the root spec directory |
| `source_parser` | Always `"openapi_parser"` |
| `api_title` | Value from `info.title` block, or `null` if missing |
| `api_version` | Value from `info.version` block, or `null` if missing |
| `api_description_summary` | First 200 characters of `info.description`, or `null` if missing |
| `servers` | List of server objects from top-level `servers` key, or empty list |

**Graceful degradation:** If YAML parsing fails or the `info` block is missing, the OpenAPI-specific fields (`api_title`, `api_version`, `api_description_summary`) are set to `null` and `servers` is set to an empty list. The document is still created with the raw text and basic metadata fields.

This metadata is included in both:
- The `NormalizedDocument.source_metadata` field
- The `NormalizedJson.source_metadata` list in the bundle

## Entity Schema

The parser extracts three types of entities from OpenAPI specs:

### Endpoint Entity

Represents an HTTP operation (path + method combination):

```json
{
  "type": "Endpoint",
  "method": "POST",
  "path": "/v1/payments",
  "operation_id": "createPayment",
  "summary": "Create a payment",
  "description": "Full description...",
  "tags": ["payments", "PIS"],
  "parameters": [
    {
      "name": "X-Request-ID",
      "location": "header",
      "required": true,
      "schema_type": "string",
      "format": "uuid",
      "description": "...",
      "deprecated": false,
      "example": null
    }
  ],
  "request_body": {...},
  "request_body_ref": "#/components/requestBodies/paymentInitiation",
  "responses": {"201": {...}, "400": {...}},
  "response_refs": {
    "201": "#/components/responses/CREATED_201_PaymentInitiation",
    "400": "#/components/responses/BAD_REQUEST_400_PIS"
  },
  "api_title": "Payment API",
  "source_file": "/path/to/spec.yaml"
}
```

**New fields:**
- `request_body_ref`: `$ref` value when the request body references a reusable component
- `response_refs`: Map of status codes to `$ref` values for response component references

### Schema Entity

Represents a data model from `components.schemas`:

```json
{
  "type": "Schema",
  "name": "PaymentRequest",
  "schema_type": "object",
  "description": "A payment request DTO",
  "source_file": "/path/to/spec.yaml",
  "properties": [
    {
      "name": "amount",
      "type": "number",
      "ref": null,
      "description": "Payment amount",
      "required": true,
      "enum_values": [],
      "format": null
    },
    {
      "name": "accountRef",
      "type": null,
      "ref": "#/components/schemas/accountReference",
      "description": null,
      "required": true,
      "enum_values": [],
      "format": null
    }
  ],
  "required": ["amount", "accountRef"],
  "enum_values": [],
  "refs": []
}
```

**Schema entity variants:**

- **Object schemas**: `schema_type: "object"`, `properties` list populated, `required` array
- **Enum schemas**: `schema_type: "string"`, `enum_values` list populated
- **Composition schemas** (allOf/oneOf/anyOf/not): `refs` list populated with `$ref` paths and `schema_composition` metadata attached for relationship extraction
- **Properties with refs**: `properties[].ref` contains `$ref` value when property type is a schema reference
- **Properties with inline enums**: `properties[].enum_values` populated when property has inline enum

All optional fields are present with empty lists or `null` values.

### Parameter Entity

Represents a reusable parameter definition from `components.parameters`:

```json
{
  "type": "Parameter",
  "name": "paymentService",
  "in": "path",
  "required": true,
  "schema_type": "string",
  "description": "Payment service type",
  "enum_values": ["payments", "bulk-payments", "periodic-payments"],
  "format": null,
  "deprecated": false,
  "example": null,
  "source_file": "/path/to/spec.yaml"
}
```

**Parameter entity variants:**

- **Path parameters**: `in: "path"`, typically `required: true`
- **Query parameters**: `in: "query"`, `required` may be `false`
- **Header parameters**: `in: "header"`, often used for request tracking or authentication
- **Cookie parameters**: `in: "cookie"`, for cookie-based state
- **Enum-constrained parameters**: `enum_values` list populated with allowed values
- **Formatted parameters**: `format` field contains JSON Schema format hint (e.g., `uuid`, `int32`)

All optional fields are present with empty lists, `false`, or `null` values.

### SecurityScheme Entity

Represents a security scheme definition from `components.securitySchemes`:

```json
{
  "type": "SecurityScheme",
  "name": "BearerAuthOAuth",
  "scheme_type": "http",
  "scheme": "bearer",
  "bearer_format": null,
  "description": "Bearer Token. Is contained only if an OAuth2 based authentication was performed.",
  "source_file": "/path/to/spec.yaml",
  "in": null,
  "parameter_name": null,
  "open_id_connect_url": null,
  "flows": {}
}
```

**SecurityScheme entity variants:**

- **HTTP bearer scheme**: `scheme_type: "http"`, `scheme: "bearer"`, optional `bearer_format: "JWT"`
- **HTTP basic scheme**: `scheme_type: "http"`, `scheme: "basic"`
- **API key scheme**: `scheme_type: "apiKey"`, `in` specifies location (`header`, `query`, `cookie`), `parameter_name` specifies the key name
- **OAuth2 scheme**: `scheme_type: "oauth2"`, `flows` contains grant type definitions (e.g., `authorizationCode`, `clientCredentials`)
- **OpenID Connect scheme**: `scheme_type: "openIdConnect"`, `open_id_connect_url` contains discovery URL

**NextGenPSD2 standard scheme:**
The `BearerAuthOAuth` HTTP bearer scheme is the standard security scheme used across all NextGenPSD2 specifications for OAuth2-based authentication.

All optional fields are present with `null` or empty dict `{}` values.

### Scope Entity

Represents an OAuth2 scope discovered from effective endpoint/operation security requirements.

```json
{
  "type": "Scope",
  "name": "payments:write",
  "properties": {
    "scope_name": "payments:write",
    "source_file": "/path/to/spec.yaml"
  }
}
```

**Scope entity notes:**

- Unique by scope name per spec output
- Created only when scope values are present in security requirements
- Used as target nodes for `REQUIRES_SCOPE` relationships

### RequestBody Entity

Represents a reusable request body definition from `components.requestBodies`:

```json
{
  "type": "RequestBody",
  "name": "paymentInitiation",
  "required": true,
  "content_types": ["application/json", "application/xml"],
  "schema_ref": "#/components/schemas/paymentInitiation_json",
  "schema_type": null,
  "description": "JSON request body for a payment initiation request message.",
  "source_file": "/path/to/spec.yaml"
}
```

**RequestBody entity fields:**
- `name`: Request body key from `components.requestBodies`
- `required`: `true` when the request body is mandatory for the operation
- `content_types`: List of supported media types (e.g., `application/json`)
- `schema_ref`: `$ref` value when the content schema is a component reference
- `schema_type`: JSON Schema type when the schema is defined inline
- `description`: Optional description of the request body

### Response Entity

Represents a reusable response definition from `components.responses`:

```json
{
  "type": "Response",
  "name": "CREATED_201_PaymentInitiation",
  "http_status": "201",
  "description": "CREATED",
  "content_types": ["application/json"],
  "schema_ref": "#/components/schemas/paymentInitiationRequestResponse-201",
  "schema_type": null,
  "headers": {},
  "source_file": "/path/to/spec.yaml"
}
```

**Response entity fields:**
- `name`: Response key from `components.responses`
- `http_status`: HTTP status code (e.g., `"201"`), extracted from name when following convention
- `description`: Required description of the response
- `content_types`: List of media types in the response (e.g., `application/json`)
- `schema_ref`: `$ref` value when the response schema is a component reference
- `schema_type`: JSON Schema type when the schema is defined inline
- `headers`: Response header definitions

All optional fields are present with empty lists, `false`, or `null` values.

## Relationship Extraction

The OpenAPI parser extracts relationships between entities to enable API dependency analysis and schema traversal. Relationships are included in the `NormalizedJson.relationships` array.

### Relationship Types

#### DEFINES

Links an API entity to every entity it owns within the same specification file.

```json
{
  "id": "uuid-string",
  "source_entity_id": "api-uuid",
  "target_entity_id": "endpoint-or-schema-uuid",
  "type": "DEFINES",
  "properties": {
    "entity_type": "Endpoint",
    "api_title": "NextGenPSD2 XS2A Framework"
  },
  "confidence": 1.0
}
```

**Direction:** API → Endpoint / Schema / DTO / Enum / SecurityScheme / RequestBody / Response / Parameter / Operation

**Use case:** Discover all entities belonging to a specification; build API dependency graphs; filter by API version

#### HAS_PARAMETER

Links endpoints to their parameters.

```json
{
  "id": "uuid-string",
  "source_entity_id": "endpoint-uuid",
  "target_entity_id": "parameter-uuid",
  "type": "HAS_PARAMETER",
  "properties": {
    "parameter_name": "accountId",
    "location": "path"
  },
  "confidence": 1.0
}
```

**Direction:** Endpoint → Parameter

**Use case:** Discover all parameters used by an endpoint

#### REFERENCES_SCHEMA

Links schemas that reference other schemas via `$ref`.

```json
{
  "id": "uuid-string",
  "source_entity_id": "source-schema-uuid",
  "target_entity_id": "target-schema-uuid",
  "type": "REFERENCES_SCHEMA",
  "properties": {
    "ref_path": "#/components/schemas/AccountReference",
    "property_name": "accountRef"
  },
  "confidence": 1.0
}
```

**Direction:** Schema → Schema

**Use case:** Schema dependency analysis, schema composition tracking

**Variants:**
- Direct schema `$ref`: `property_name` is absent
- Property `$ref`: `property_name` indicates which property references the target schema

#### ACCEPTS

Links endpoints to request body schemas.

```json
{
  "id": "uuid-string",
  "source_entity_id": "endpoint-uuid",
  "target_entity_id": "schema-uuid",
  "type": "ACCEPTS",
  "properties": {
    "ref_path": "#/components/schemas/PaymentRequest"
  },
  "confidence": 1.0
}
```

**Direction:** Endpoint → Schema

**Use case:** Discover the request schema for an endpoint operation

#### RETURNS

Links endpoints to response schemas.

```json
{
  "id": "uuid-string",
  "source_entity_id": "endpoint-uuid",
  "target_entity_id": "schema-uuid",
  "type": "RETURNS",
  "properties": {
    "status_code": "201",
    "ref_path": "#/components/schemas/PaymentResponse"
  },
  "confidence": 1.0
}
```

**Direction:** Endpoint → Schema

**Use case:** Discover response schemas for each HTTP status code

**Note:** An endpoint may have multiple RETURNS relationships (one per response status code).

#### REQUIRES_SECURITY

Links endpoints and operations to required security schemes.

```json
{
  "id": "uuid-string",
  "source_entity_id": "endpoint-or-operation-uuid",
  "target_entity_id": "security-scheme-uuid",
  "type": "REQUIRES_SECURITY",
  "properties": {
    "security_scheme": "BearerAuthOAuth",
    "endpoint_path": "/v1/payments",
    "endpoint_method": "POST",
    "operation_id": "initiatePayment",
    "scopes": ["payments:write"],
    "required": true,
    "optional": false,
    "logic": "AND",
    "alternatives": 1
  },
  "confidence": 1.0
}
```

**Direction:** Endpoint/Operation → SecurityScheme

**Use case:** Security requirement analysis, authentication flow documentation, coverage checks

#### REQUIRES_SCOPE

Links endpoints and operations to required OAuth2 scopes.

```json
{
  "id": "uuid-string",
  "source_entity_id": "endpoint-or-operation-uuid",
  "target_entity_id": "scope-uuid",
  "type": "REQUIRES_SCOPE",
  "properties": {
    "scope_name": "payments:write",
    "security_scheme": "OAuth2",
    "endpoint_path": "/v1/payments",
    "endpoint_method": "POST",
    "operation_id": "initiatePayment"
  },
  "confidence": 1.0
}
```

**Direction:** Endpoint/Operation → Scope

**Use case:** OAuth2 authorization analysis and scope coverage verification

### Relationship Extraction Implementation

Relationships are extracted by the `relationship_builder` module after entity extraction. The builder:

1. Indexes entities by type and name for efficient lookup
2. Extracts relationship types in parallel:
   - `HAS_PARAMETER` from endpoint parameter lists
   - `REFERENCES_SCHEMA` from schema `$ref` fields and property `$ref` fields
   - `ACCEPTS` from endpoint `request_body_ref` fields
   - `RETURNS` from endpoint `response_refs` mappings
   - `REQUIRES_SECURITY` from effective endpoint and operation security requirements
   - `REQUIRES_SCOPE` from OAuth2 scopes in effective security requirements
3. Returns a list of relationship dictionaries for inclusion in `NormalizedJson`

Security requirements are resolved with OpenAPI precedence:

- Operation-level `security` overrides path/global
- Path-level `security` overrides global
- Global `security` applies as fallback
- Requirement object entries are interpreted as AND logic
- Requirement array entries are interpreted as OR logic
- Empty requirement object (`{}`) is treated as optional/public alternative

### Schema Composition Relationships

Schema composition keywords are emitted as explicit schema-to-schema relationships:

- `COMPOSES_ALL_OF` for `allOf`
- `ONE_OF` for `oneOf`
- `ANY_OF` for `anyOf`
- `NOT` for `not`

Relationship properties include:

- `composition_type`
- `position` (for list-based compositions)
- `schema_name`
- `composed_schema`
- `ref_path`
- `discriminator` (for `oneOf` when `discriminator.propertyName` is present)
- `path` (composition nesting path for nested compositions)

Inline composition entries are traversed recursively so nested compositions are captured.

**Module:** `openapi_parser.relationship_builder`

**Tests:** `openapi_parser.tests.test_relationship_builder`

### Relationship Coverage

The parser extracts relationships for:
- ✅ API-entity ownership relationships (`DEFINES`)
- ✅ Endpoint-parameter relationships
- ✅ Schema-schema references (via `$ref`)
- ✅ Endpoint-schema relationships (request/response)
- ✅ Endpoint/operation-security relationships (`REQUIRES_SECURITY`)
- ✅ Endpoint/operation-scope relationships (`REQUIRES_SCOPE`)
- ✅ Schema composition relationships (allOf/oneOf/anyOf/not)
- ❌ Property type relationships — future enhancement

### Example: Complete Endpoint Relationships

Given an endpoint `POST /v1/payments`:

```
Endpoint: POST /v1/payments
  HAS_PARAMETER → Parameter: X-Request-ID (header)
  HAS_PARAMETER → Parameter: paymentService (path)
  ACCEPTS → Schema: PaymentRequest
  RETURNS (201) → Schema: PaymentResponse
  RETURNS (400) → Schema: Error400
  REQUIRES_SECURITY → SecurityScheme: BearerAuthOAuth
```

The extracted relationships enable:
- API contract validation
- Schema dependency analysis
- Security requirement tracking
- Request/response schema discovery
- Parameter usage analysis



