# OpenAPI Parser: Separate Response Entities

## Priority

**High**

## Goal

Extract responses as separate first-class entities rather than embedding them in Endpoint entities.

## Current Issue

Response information is currently embedded in Endpoint entities:

```json
{
  "type": "Endpoint",
  "method": "POST",
  "path": "/v1/payments",
  "responses": {
    "201": {
      "description": "Payment created",
      "content": {
        "application/json": {
          "schema": {...}
        }
      }
    },
    "400": {
      "description": "Bad request"
    }
  }
}
```

This embedding prevents:
- Reusable response definitions
- Response entity queries
- Response relationships to schemas
- Response versioning tracking
- Shared responses across endpoints
- Status code analysis

## Expected Behavior

Responses should be separate `Response` entities:

```json
{
  "type": "Response",
  "name": "201 PaymentCreated",
  "id": "uuid-of-response",
  "source": "openapi_parser:psd2-api:v1.3.16:response:PaymentCreated",
  "properties": {
    "status_code": "201",
    "description": "Payment created successfully",
    "content_types": ["application/json"],
    "source_file": "/path/to/spec.yaml",
    "reusable": true,
    "ref_path": "#/components/responses/PaymentCreated"
  }
}
```

For error responses:

```json
{
  "type": "Response",
  "name": "400 BadRequest",
  "id": "uuid-of-error-response",
  "source": "openapi_parser:psd2-api:v1.3.16:response:BadRequest",
  "properties": {
    "status_code": "400",
    "description": "Bad request - invalid payment data",
    "content_types": ["application/json"],
    "is_error": true,
    "error_category": "client_error"
  }
}
```

Relationships to create:

```json
{
  "type": "HAS_RESPONSE",
  "source_entity_id": "uuid-of-endpoint",
  "target_entity_id": "uuid-of-response",
  "properties": {
    "endpoint_path": "/v1/payments",
    "endpoint_method": "POST",
    "status_code": "201"
  }
}
```

```json
{
  "type": "USES_SCHEMA",
  "source_entity_id": "uuid-of-response",
  "target_entity_id": "uuid-of-schema",
  "properties": {
    "content_type": "application/json",
    "schema_name": "PaymentInitiationResponse"
  }
}
```

## Required Implementation

1. Create `ResponseEntityBuilder` in `POC/2_Parsers/openapi_parser/`
2. Extract responses from:
   - Inline definitions in path operations
   - Shared definitions in `#/components/responses`
3. Build Response entities with metadata
4. Categorize responses:
   - Success (2xx)
   - Client error (4xx)
   - Server error (5xx)
5. Replace embedded responses in Endpoint entities with references
6. Build `HAS_RESPONSE` relationships
7. Build `USES_SCHEMA` relationships from Response to Schema
8. Handle multiple content types
9. Deduplicate reusable responses

## Validation Checklist

- [ ] Response entities created for all endpoint responses
- [ ] Inline responses extracted
- [ ] Shared responses extracted from components
- [ ] Response description preserved
- [ ] Status codes captured
- [ ] Content types captured
- [ ] Error responses marked with `is_error: true`
- [ ] `HAS_RESPONSE` relationships created
- [ ] `USES_SCHEMA` relationships created
- [ ] Multiple responses per endpoint handled
- [ ] Reusable responses not duplicated

## Testing Requirements

1. Unit test: inline response extraction
2. Unit test: shared response extraction
3. Unit test: success response (2xx)
4. Unit test: error response (4xx, 5xx)
5. Unit test: response with multiple content types
6. Unit test: response without schema
7. Unit test: multiple responses for one endpoint
8. Integration test: all endpoints have Response entities
9. Integration test: verify HAS_RESPONSE relationships
10. Integration test: verify USES_SCHEMA relationships

## Documentation Updates

Update `POC/2_Parsers/openapi_parser/README.md`:
- Add Response to entity list
- Document HAS_RESPONSE relationship
- Document USES_SCHEMA relationship
- Explain inline vs shared responses
- Document status code categorization
- Document content type handling
