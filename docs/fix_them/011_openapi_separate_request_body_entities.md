# OpenAPI Parser: Separate Request Body Entities

## Priority

**High**

## Goal

Extract request bodies as separate first-class entities rather than embedding them in Endpoint entities.

## Current Issue

Request body information is currently embedded in Endpoint entities:

```json
{
  "type": "Endpoint",
  "method": "POST",
  "path": "/v1/payments",
  "request_body": {
    "description": "Payment initiation request",
    "required": true,
    "content": {
      "application/json": {
        "schema": {...}
      }
    }
  }
}
```

This embedding prevents:
- Reusable request body definitions
- Request body entity queries
- Request body relationships to schemas
- Request body versioning tracking
- Shared request bodies across endpoints

## Expected Behavior

Request bodies should be separate `RequestBody` entities:

```json
{
  "type": "RequestBody",
  "name": "PaymentInitiationRequest",
  "id": "uuid-of-request-body",
  "source": "openapi_parser:psd2-api:v1.3.16:requestBody:PaymentInitiationRequest",
  "properties": {
    "description": "Payment initiation request body",
    "required": true,
    "content_types": ["application/json", "application/xml"],
    "source_file": "/path/to/spec.yaml",
    "reusable": true,
    "ref_path": "#/components/requestBodies/PaymentInitiationRequest"
  }
}
```

Relationships to create:

```json
{
  "type": "HAS_REQUEST_BODY",
  "source_entity_id": "uuid-of-endpoint",
  "target_entity_id": "uuid-of-request-body",
  "properties": {
    "endpoint_path": "/v1/payments",
    "endpoint_method": "POST",
    "required": true
  }
}
```

```json
{
  "type": "USES_SCHEMA",
  "source_entity_id": "uuid-of-request-body",
  "target_entity_id": "uuid-of-schema",
  "properties": {
    "content_type": "application/json",
    "schema_name": "PaymentInitiation"
  }
}
```

## Required Implementation

1. Create `RequestBodyEntityBuilder` in `POC/2_Parsers/openapi_parser/`
2. Extract request bodies from:
   - Inline definitions in path operations
   - Shared definitions in `#/components/requestBodies`
3. Build RequestBody entities with metadata
4. Replace embedded request_body in Endpoint entities with reference
5. Build `HAS_REQUEST_BODY` relationships
6. Build `USES_SCHEMA` relationships from RequestBody to Schema
7. Handle multiple content types (application/json, application/xml, etc.)
8. Deduplicate reusable request bodies

## Validation Checklist

- [ ] RequestBody entities created for all endpoints with request bodies
- [ ] Inline request bodies extracted
- [ ] Shared request bodies extracted from components
- [ ] Request body description preserved
- [ ] Required flag preserved
- [ ] Content types captured
- [ ] `HAS_REQUEST_BODY` relationships created
- [ ] `USES_SCHEMA` relationships created
- [ ] Multiple content types handled
- [ ] Reusable request bodies not duplicated

## Testing Requirements

1. Unit test: inline request body extraction
2. Unit test: shared request body extraction
3. Unit test: request body with multiple content types
4. Unit test: required vs optional request body
5. Unit test: request body with complex schema
6. Integration test: all POST/PUT/PATCH endpoints have RequestBody entities
7. Integration test: verify HAS_REQUEST_BODY relationships
8. Integration test: verify USES_SCHEMA relationships

## Documentation Updates

Update `POC/2_Parsers/openapi_parser/README.md`:
- Add RequestBody to entity list
- Document HAS_REQUEST_BODY relationship
- Document USES_SCHEMA relationship
- Explain inline vs shared request bodies
- Document content type handling
