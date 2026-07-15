# Java Parser: Missing Parameter Type Relationships

## Priority

**Medium**

## Goal

Add `HAS_TYPE` relationships from Parameter entities to their declared types.

## Current Issue

Parameter entities store type as a string property:

```json
{
  "type": "Parameter",
  "name": "profileId",
  "parameter_type": "String",
  "position": 0
}
```

There is no `HAS_TYPE` relationship linking the parameter to its type entity.

This prevents:
- Parameter type dependency tracking
- API signature analysis
- Type compatibility checking
- Refactoring impact analysis

## Expected Behavior

Every Parameter entity should have a `HAS_TYPE` relationship to its declared type:

```json
{
  "type": "HAS_TYPE",
  "source": "uuid-of-parameter-profileId",
  "target": "uuid-of-class-String",
  "properties": {
    "parameter_name": "profileId",
    "type_name": "String",
    "is_collection": false,
    "is_generic": false,
    "is_varargs": false
  }
}
```

For generic parameter types:

```json
{
  "type": "HAS_TYPE",
  "source": "uuid-of-parameter-accounts",
  "target": "uuid-of-class-List",
  "properties": {
    "parameter_name": "accounts",
    "type_name": "List<Account>",
    "is_collection": true,
    "is_generic": true,
    "generic_arguments": ["Account"]
  }
}
```

For varargs parameters:

```json
{
  "type": "HAS_TYPE",
  "source": "uuid-of-parameter-values",
  "target": "uuid-of-class-String",
  "properties": {
    "parameter_name": "values",
    "type_name": "String...",
    "is_varargs": true,
    "is_collection": true
  }
}
```

## Required Implementation

1. Create `ParameterTypeRelationshipBuilder` in `POC/2_Parsers/java_parser/`
2. For each Parameter entity:
   - Parse the parameter type declaration
   - Resolve the fully qualified type name
   - Find or create the target type entity
   - Build `HAS_TYPE` relationship
3. Handle generic parameter types
4. Handle collection parameter types
5. Handle array parameter types
6. Handle primitive parameter types
7. Handle varargs parameters (e.g., `String... values`)

## Validation Checklist

- [ ] Simple type relationship created: `String name` → `HAS_TYPE` → String
- [ ] Custom type relationship created: `Account account` → `HAS_TYPE` → Account
- [ ] Generic type handled: `List<Account> accounts` → `HAS_TYPE` → List
- [ ] Array type handled: `String[] names` → `HAS_TYPE` → String
- [ ] Primitive type handled: `int count` → `HAS_TYPE` → int
- [ ] Varargs handled: `String... values` → `HAS_TYPE` → String with `is_varargs: true`
- [ ] Collection metadata preserved in relationship properties
- [ ] Generic arguments preserved in relationship properties
- [ ] Relationship points to correct target entity UUID

## Testing Requirements

1. Unit test: simple parameter type relationship
2. Unit test: custom class parameter type
3. Unit test: generic parameter type
4. Unit test: array parameter type
5. Unit test: primitive parameter type
6. Unit test: varargs parameter type
7. Unit test: nested generic parameter type: `Map<String, List<Account>>`
8. Integration test: all Parameter entities have HAS_TYPE relationships
9. Integration test: relationships point to valid type entities

## Documentation Updates

Update `POC/2_Parsers/java_parser/README.md`:
- Add HAS_TYPE for parameters to relationship list
- Document parameter type handling
- Document varargs handling
- Explain generic parameter type extraction
