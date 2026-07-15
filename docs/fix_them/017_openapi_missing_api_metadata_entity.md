# OpenAPI Parser: Missing API Metadata Entity

## Priority

**Low**

## Goal

Extract OpenAPI `info` block as a dedicated `API` entity.

## Current Issue

API-level metadata (title, version, description, contact, license) is captured in `source_metadata` but not as a dedicated entity:

```json
{
  "source_metadata": {
    "api_title": "NextGenPSD2 XS2A Framework",
    "api_version": "1.3.16_2025-11-27",
    "servers": [...]
  }
}
```

This metadata is not queryable as an entity and cannot be related to other entities.

Without API entities:
- Cannot query specifications by API name
- Cannot track API versions as entities
- Cannot relate APIs to their endpoints
- Cannot build API dependency graphs

## Expected Behavior

Create a dedicated `API` entity for each parsed specification:

```json
{
  "type": "API",
  "name": "NextGenPSD2 XS2A Framework",
  "id": "uuid-of-api",
  "source": "openapi_parser:psd2-api:v1.3.16",
  "properties": {
    "title": "NextGenPSD2 XS2A Framework",
    "version": "1.3.16_2025-11-27",
    "description": "The NextGenPSD2 Framework offers...",
    "contact_name": null,
    "contact_email": null,
    "contact_url": null,
    "license_name": null,
    "license_url": null,
    "terms_of_service": null,
    "openapi_version": "3.0.1",
    "source_file": "/path/to/spec.yaml"
  }
}
```

Relationships to create:

```json
{
  "type": "DEFINES",
  "source_entity_id": "uuid-of-api",
  "target_entity_id": "uuid-of-endpoint",
  "properties": {
    "entity_type": "Endpoint"
  }
}
```

```json
{
  "type": "DEFINES",
  "source_entity_id": "uuid-of-api",
  "target_entity_id": "uuid-of-dto",
  "properties": {
    "entity_type": "DTO"
  }
}
```

```json
{
  "type": "HAS_VERSION",
  "source_entity_id": "uuid-of-api",
  "target_entity_id": "uuid-of-version",
  "properties": {
    "version": "1.3.16_2025-11-27",
    "openapi_version": "3.0.1"
  }
}
```

## Required Implementation

1. Create `ApiEntityBuilder` in `POC/2_Parsers/openapi_parser/`
2. Extract `info` block from OpenAPI spec
3. Build API entity with:
   - title
   - version
   - description
   - contact info
   - license info
   - terms of service
   - OpenAPI version
4. Build `DEFINES` relationships from API to all extracted entities
5. Build `HAS_SERVER` relationships to server entities (if servers are entities)
6. Create one API entity per parsed specification file

## Validation Checklist

- [ ] API entity created for each parsed specification
- [ ] Title captured
- [ ] Version captured
- [ ] Description captured
- [ ] Contact info captured
- [ ] License info captured
- [ ] OpenAPI version captured
- [ ] Source file path captured
- [ ] `DEFINES` relationships created to all endpoints
- [ ] `DEFINES` relationships created to all schemas/DTOs

## Testing Requirements

1. Unit test: API entity extraction
2. Unit test: API with contact info
3. Unit test: API with license info
4. Unit test: API without optional fields
5. Integration test: one API entity per specification file
6. Integration test: verify DEFINES relationships cover all entities
7. Integration test: verify API metadata matches spec info block

## Documentation Updates

Update `POC/2_Parsers/openapi_parser/README.md`:
- Add API to entity list
- Document DEFINES relationship
- Document HAS_SERVER relationship (if applicable)
- Explain one API entity per specification
- Document info block extraction
