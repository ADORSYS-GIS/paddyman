# OpenAPI Parser: Separate Operation Entities

## Priority

**Medium**

## Goal

Extract operations as separate entities distinct from endpoints, representing the logical operation metadata.

## Current Issue

Endpoint entities conflate the HTTP method+path combination with the operation metadata:

```json
{
  "type": "Endpoint",
  "method": "POST",
  "path": "/v1/payments",
  "operation_id": "initiatePayment",
  "description": "...",
  "tags": ["payments"]
}
```

In OpenAPI specifications, an operation represents:
- A unique operation ID (used for code generation)
- Operation-level metadata (tags, description, summary)
- Operation-level security requirements
- Deprecated flag

Separating operations from endpoints enables:
- Operation-level queries
- Operation grouping by tags
- Code generation traceability
- Operation deprecation tracking

## Expected Behavior

Operations should be separate `Operation` entities:

```json
{
  "type": "Operation",
  "name": "initiatePayment",
  "id": "uuid-of-operation",
  "source": "openapi_parser:psd2-api:v1.3.16:operation:initiatePayment",
  "properties": {
    "operation_id": "initiatePayment",
    "summary": "Initiate a payment",
    "description": "This operation initiates a payment at the ASPSP...",
    "tags": ["payments", "PIS"],
    "deprecated": false,
    "external_docs": null,
    "source_file": "/path/to/spec.yaml"
  }
}
```

Relationships to create:

```json
{
  "type": "IMPLEMENTS_OPERATION",
  "source_entity_id": "uuid-of-endpoint",
  "target_entity_id": "uuid-of-operation",
  "properties": {
    "method": "POST",
    "path": "/v1/payments"
  }
}
```

```json
{
  "type": "TAGGED_AS",
  "source_entity_id": "uuid-of-operation",
  "target_entity_id": "uuid-of-tag",
  "properties": {
    "tag_name": "payments"
  }
}
```

## Required Implementation

1. Create `OperationEntityBuilder` in `POC/2_Parsers/openapi_parser/`
2. Extract operation metadata from each path operation
3. Build Operation entities with:
   - operation_id
   - summary
   - description
   - tags
   - deprecated flag
   - external docs
4. Create Tag entities for unique tags
5. Build `IMPLEMENTS_OPERATION` relationships from Endpoint to Operation
6. Build `TAGGED_AS` relationships from Operation to Tag
7. Handle operations without operation_id (generate placeholder)
8. Preserve operation order in spec

## Validation Checklist

- [ ] Operation entities created for all path operations
- [ ] operation_id preserved
- [ ] summary and description preserved
- [ ] tags captured
- [ ] deprecated flag captured
- [ ] external docs captured
- [ ] `IMPLEMENTS_OPERATION` relationships created
- [ ] `TAGGED_AS` relationships created
- [ ] Tag entities created for unique tags
- [ ] Operations without operation_id handled gracefully

## Testing Requirements

1. Unit test: operation with all metadata
2. Unit test: operation without operation_id
3. Unit test: deprecated operation
4. Unit test: operation with multiple tags
5. Unit test: operation with external docs
6. Integration test: all endpoints have IMPLEMENTS_OPERATION relationships
7. Integration test: all tags appear as Tag entities
8. Integration test: verify operation_id uniqueness

## Documentation Updates

Update `POC/2_Parsers/openapi_parser/README.md`:
- Add Operation to entity list
- Add Tag to entity list
- Document IMPLEMENTS_OPERATION relationship
- Document TAGGED_AS relationship
- Explain operation vs endpoint distinction
