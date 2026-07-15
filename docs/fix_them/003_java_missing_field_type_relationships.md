# Java Parser: Missing Field Type Relationships

## Priority

**Medium**

## Goal

Add `HAS_TYPE` relationships from Field entities to their declared types.

## Current Issue

Field entities capture field names and basic metadata but lack explicit relationships to their types:

```json
{
  "type": "Field",
  "name": "ais",
  "field_type": "AisAspspProfileSetting",
  "file_path": "...",
  "start_line": 34,
  "end_line": 34
}
```

The `field_type` is stored as a string property, but there is no `HAS_TYPE` relationship linking the Field entity to the corresponding Class/Interface/Enum entity.

This prevents:
- Type dependency graph construction
- Data flow analysis
- Type usage tracking
- Refactoring impact analysis

## Expected Behavior

Every Field entity should have a `HAS_TYPE` relationship to its declared type:

```json
{
  "type": "HAS_TYPE",
  "source": "uuid-of-field-ais",
  "target": "uuid-of-class-AisAspspProfileSetting",
  "properties": {
    "field_name": "ais",
    "type_name": "AisAspspProfileSetting",
    "is_collection": false,
    "is_generic": false
  }
}
```

For generic types:

```json
{
  "type": "HAS_TYPE",
  "source": "uuid-of-field-accounts",
  "target": "uuid-of-class-List",
  "properties": {
    "field_name": "accounts",
    "type_name": "List<AccountReference>",
    "is_collection": true,
    "is_generic": true,
    "generic_arguments": ["AccountReference"]
  }
}
```

## Required Implementation

1. Create `FieldTypeRelationshipBuilder` in `POC/2_Parsers/java_parser/`
2. For each Field entity:
   - Parse the field type declaration
   - Resolve the fully qualified type name
   - Find or create the target type entity
   - Build `HAS_TYPE` relationship
3. Handle generic types: extract base type and type arguments
4. Handle collection types: `List<T>`, `Set<T>`, `Map<K,V>`
5. Handle array types: `String[]`, `int[]`
6. Handle primitive types: create primitive type entities if needed

## Validation Checklist

- [ ] Simple type relationship created: `String name` → `HAS_TYPE` → String
- [ ] Custom type relationship created: `AisAspspProfileSetting ais` → `HAS_TYPE` → AisAspspProfileSetting
- [ ] Generic type handled: `List<Account>` → `HAS_TYPE` → List
- [ ] Array type handled: `String[] names` → `HAS_TYPE` → String
- [ ] Primitive type handled: `int count` → `HAS_TYPE` → int
- [ ] Collection metadata preserved in relationship properties
- [ ] Generic arguments preserved in relationship properties
- [ ] Relationship points to correct target entity UUID

## Testing Requirements

1. Unit test: simple field type relationship
2. Unit test: custom class field type
3. Unit test: generic field type
4. Unit test: array field type
5. Unit test: primitive field type
6. Unit test: nested generic type: `Map<String, List<Account>>`
7. Integration test: all Field entities have HAS_TYPE relationships
8. Integration test: relationships point to valid type entities

## Documentation Updates

Update `POC/2_Parsers/java_parser/README.md`:
- Add HAS_TYPE to relationship list
- Document generic type handling
- Document collection type handling
- Explain primitive type entity creation
