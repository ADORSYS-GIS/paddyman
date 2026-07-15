# OpenAPI Parser: DTO and Enum Entities

## Priority

**Medium**

## Goal

Distinguish DTO (Data Transfer Object) and Enum entities from generic Schema entities.

## Current Issue

All schemas are currently represented as generic `Schema` entities:

```json
{
  "type": "Schema",
  "name": "PaymentInitiation",
  "schema_type": "object",
  "properties": []
}
```

```json
{
  "type": "Schema",
  "name": "PaymentProduct",
  "schema_type": "string",
  "enum_values": ["sepa-credit-transfers", "instant-sepa-credit-transfers"]
}
```

This loses semantic information:
- Object schemas with properties are DTOs
- String schemas with enum values are Enums
- Primitive schemas are simple types

Distinguishing these enables:
- DTO-specific queries
- Enum-specific queries
- Code generation targeting
- Type category analysis

## Expected Behavior

DTOs should be `DTO` entities:

```json
{
  "type": "DTO",
  "name": "PaymentInitiation",
  "id": "uuid-of-dto",
  "source": "openapi_parser:psd2-api:v1.3.16:dto:PaymentInitiation",
  "properties": {
    "description": "Payment initiation request",
    "required_fields": ["debtorAccount", "instructedAmount", "creditorAccount"],
    "property_count": 12,
    "source_file": "/path/to/spec.yaml",
    "ref_path": "#/components/schemas/PaymentInitiation"
  }
}
```

Enums should be `Enum` entities:

```json
{
  "type": "Enum",
  "name": "PaymentProduct",
  "id": "uuid-of-enum",
  "source": "openapi_parser:psd2-api:v1.3.16:enum:PaymentProduct",
  "properties": {
    "description": "Supported payment products",
    "values": [
      "sepa-credit-transfers",
      "instant-sepa-credit-transfers",
      "target-2-payments",
      "cross-border-credit-transfers"
    ],
    "value_count": 4,
    "base_type": "string"
  }
}
```

Relationships to create:

```json
{
  "type": "HAS_PROPERTY",
  "source_entity_id": "uuid-of-dto",
  "target_entity_id": "uuid-of-property-schema",
  "properties": {
    "property_name": "debtorAccount",
    "required": true,
    "nullable": false
  }
}
```

```json
{
  "type": "HAS_ENUM_VALUE",
  "source_entity_id": "uuid-of-enum",
  "target_entity_id": "uuid-of-enum-value",
  "properties": {
    "value": "sepa-credit-transfers",
    "position": 0
  }
}
```

## Required Implementation

1. Create `DtoEntityBuilder` in `POC/2_Parsers/openapi_parser/`
2. Create `EnumEntityBuilder` in `POC/2_Parsers/openapi_parser/`
3. Classify schemas:
   - Object schemas with properties → DTO
   - Schemas with enum values → Enum
   - Other schemas → remain as Schema
4. Build DTO entities with property metadata
5. Build Enum entities with enum values
6. Build `HAS_PROPERTY` relationships from DTO to property schemas
7. Build `HAS_ENUM_VALUE` relationships (or store values in properties)
8. Preserve all existing Schema metadata

## Validation Checklist

- [ ] Object schemas become DTO entities
- [ ] Enum schemas become Enum entities
- [ ] Simple schemas remain Schema entities
- [ ] DTO property count accurate
- [ ] DTO required fields captured
- [ ] Enum values captured
- [ ] Enum value count accurate
- [ ] `HAS_PROPERTY` relationships created
- [ ] Base type preserved for enums
- [ ] Description preserved for DTOs and Enums

## Testing Requirements

1. Unit test: object schema → DTO entity
2. Unit test: enum schema → Enum entity
3. Unit test: simple schema remains Schema
4. Unit test: DTO with required fields
5. Unit test: DTO with optional fields
6. Unit test: enum with string values
7. Unit test: enum with numeric values
8. Integration test: verify DTO count matches object schemas
9. Integration test: verify Enum count matches enum schemas
10. Integration test: verify HAS_PROPERTY relationships

## Documentation Updates

Update `POC/2_Parsers/openapi_parser/README.md`:
- Add DTO to entity list
- Add Enum to entity list
- Document HAS_PROPERTY relationship
- Document HAS_ENUM_VALUE relationship (if applicable)
- Explain schema classification logic
