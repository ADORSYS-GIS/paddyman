# OpenAPI Parser: Schema Composition Relationships

## Priority

**Medium**

## Goal

Extract schema composition relationships (allOf, oneOf, anyOf, not) as explicit relationships.

## Current Issue

Schema composition keywords (`allOf`, `oneOf`, `anyOf`, `not`) define how schemas relate to each other but are not currently extracted as relationships.

Examples:

```yaml
PaymentResponse:
  allOf:
    - $ref: '#/components/schemas/BaseResponse'
    - type: object
      properties:
        paymentId:
          type: string
```

```yaml
PaymentProduct:
  oneOf:
    - $ref: '#/components/schemas/SepaPayment'
    - $ref: '#/components/schemas/InstantPayment'
```

Without composition relationships:
- Schema inheritance is not visible
- Polymorphic schemas are not linked
- Schema validation logic is incomplete
- DTO hierarchy is lost

## Expected Behavior

Composition relationships should be explicit:

For `allOf` (inheritance/composition):

```json
{
  "type": "COMPOSES_ALL_OF",
  "source_entity_id": "uuid-of-PaymentResponse",
  "target_entity_id": "uuid-of-BaseResponse",
  "properties": {
    "composition_type": "allOf",
    "position": 0,
    "schema_name": "PaymentResponse",
    "composed_schema": "BaseResponse"
  }
}
```

For `oneOf` (polymorphism):

```json
{
  "type": "ONE_OF",
  "source_entity_id": "uuid-of-PaymentProduct",
  "target_entity_id": "uuid-of-SepaPayment",
  "properties": {
    "composition_type": "oneOf",
    "position": 0,
    "discriminator": null
  }
}
```

For `anyOf`:

```json
{
  "type": "ANY_OF",
  "source_entity_id": "uuid-of-PaymentMethod",
  "target_entity_id": "uuid-of-CardPayment",
  "properties": {
    "composition_type": "anyOf",
    "position": 0
  }
}
```

For `not`:

```json
{
  "type": "NOT",
  "source_entity_id": "uuid-of-NonEmptyString",
  "target_entity_id": "uuid-of-EmptyString",
  "properties": {
    "composition_type": "not"
  }
}
```

## Required Implementation

1. Create `SchemaCompositionRelationshipBuilder` in `POC/2_Parsers/openapi_parser/`
2. Detect composition keywords in schema definitions:
   - `allOf`
   - `oneOf`
   - `anyOf`
   - `not`
3. For each composition:
   - Resolve referenced schemas
   - Build appropriate relationship type
   - Preserve composition position
   - Capture discriminator (if present for oneOf)
4. Handle inline schemas within composition
5. Handle nested composition

## Validation Checklist

- [ ] `allOf` compositions extracted
- [ ] `oneOf` compositions extracted
- [ ] `anyOf` compositions extracted
- [ ] `not` compositions extracted
- [ ] Multiple composed schemas handled
- [ ] Position preserved
- [ ] Discriminator captured (for oneOf)
- [ ] Inline schemas within composition handled
- [ ] Nested composition handled
- [ ] Relationships point to correct schema entities

## Testing Requirements

1. Unit test: allOf composition
2. Unit test: oneOf composition
3. Unit test: anyOf composition
4. Unit test: not composition
5. Unit test: allOf with multiple schemas
6. Unit test: oneOf with discriminator
7. Unit test: nested composition
8. Integration test: all compositions in spec have relationships
9. Integration test: verify composition hierarchy is correct

## Documentation Updates

Update `POC/2_Parsers/openapi_parser/README.md`:
- Add COMPOSES_ALL_OF to relationship list
- Add ONE_OF to relationship list
- Add ANY_OF to relationship list
- Add NOT to relationship list
- Document composition relationship types
- Explain discriminator handling
