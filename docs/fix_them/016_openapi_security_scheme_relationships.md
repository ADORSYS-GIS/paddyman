# OpenAPI Parser: Security Scheme Relationships

## Priority

**Low**

## Goal

Add relationships from Endpoint/Operation entities to SecurityScheme entities.

## Current Issue

SecurityScheme entities exist:

```json
{
  "type": "SecurityScheme",
  "name": "BearerAuth",
  "properties": {
    "scheme_type": "http",
    "scheme": "bearer",
    "bearer_format": "JWT"
  }
}
```

However, there are no relationships linking:
- Endpoints to required security schemes
- Operations to required security schemes
- Security schemes to their usage points

This prevents:
- Security requirement tracking
- Authorization analysis
- Access control visualization
- Security coverage verification

## Expected Behavior

Security relationships should be explicit:

For endpoint-level security:

```json
{
  "type": "REQUIRES_SECURITY",
  "source_entity_id": "uuid-of-endpoint",
  "target_entity_id": "uuid-of-security-scheme",
  "properties": {
    "endpoint_path": "/v1/payments",
    "endpoint_method": "POST",
    "security_scheme": "BearerAuth",
    "scopes": ["payments:write"],
    "required": true
  }
}
```

For operation-level security:

```json
{
  "type": "REQUIRES_SECURITY",
  "source_entity_id": "uuid-of-operation",
  "target_entity_id": "uuid-of-security-scheme",
  "properties": {
    "operation_id": "initiatePayment",
    "security_scheme": "BearerAuth",
    "scopes": ["payments:write"],
    "required": true
  }
}
```

For OAuth2 scopes:

```json
{
  "type": "REQUIRES_SCOPE",
  "source_entity_id": "uuid-of-endpoint",
  "target_entity_id": "uuid-of-scope",
  "properties": {
    "scope_name": "payments:write",
    "security_scheme": "OAuth2"
  }
}
```

## Required Implementation

1. Create `SecurityRelationshipBuilder` in `POC/2_Parsers/openapi_parser/`
2. Extract security requirements from:
   - Global security definitions
   - Path-level security overrides
   - Operation-level security overrides
3. Build `REQUIRES_SECURITY` relationships
4. Extract OAuth2 scopes
5. Create Scope entities for unique scopes
6. Build `REQUIRES_SCOPE` relationships
7. Handle multiple security schemes (AND logic)
8. Handle optional security (OR logic)

## Validation Checklist

- [ ] Global security requirements extracted
- [ ] Operation-level security requirements extracted
- [ ] `REQUIRES_SECURITY` relationships created
- [ ] OAuth2 scopes captured
- [ ] Scope entities created
- [ ] `REQUIRES_SCOPE` relationships created
- [ ] Multiple security schemes handled (AND)
- [ ] Optional security handled (OR)
- [ ] Security scheme names match actual definitions

## Testing Requirements

1. Unit test: endpoint with single security scheme
2. Unit test: endpoint with multiple security schemes
3. Unit test: endpoint with OAuth2 scopes
4. Unit test: operation overriding global security
5. Unit test: endpoint with no security (public)
6. Integration test: all secured endpoints have REQUIRES_SECURITY relationships
7. Integration test: all OAuth2 scopes appear as entities
8. Integration test: verify security coverage

## Documentation Updates

Update `POC/2_Parsers/openapi_parser/README.md`:
- Add REQUIRES_SECURITY to relationship list
- Add REQUIRES_SCOPE to relationship list
- Add Scope to entity list
- Document security relationship extraction
- Explain OAuth2 scope handling
- Document AND/OR security logic
