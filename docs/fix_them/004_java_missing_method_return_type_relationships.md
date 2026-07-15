# Java Parser: Missing Method Return Type Relationships

## Priority

**Medium**

## Goal

Add `RETURNS` relationships from Method entities to their return types.

## Current Issue

Method entities store return type as a string property:

```json
{
  "type": "Method",
  "name": "getAspspSettings",
  "return_type": "AspspSettings",
  "start_line": 36,
  "end_line": 36
}
```

There is no `RETURNS` relationship linking the method to the return type entity.

This prevents:
- Return type dependency tracking
- API contract analysis
- Type flow analysis
- Refactoring impact analysis

## Expected Behavior

Every Method entity should have a `RETURNS` relationship to its return type:

```json
{
  "type": "RETURNS",
  "source": "uuid-of-method-getAspspSettings",
  "target": "uuid-of-class-AspspSettings",
  "properties": {
    "method_name": "getAspspSettings",
    "return_type": "AspspSettings",
    "is_collection": false,
    "is_generic": false,
    "is_void": false
  }
}
```

For generic return types:

```json
{
  "type": "RETURNS",
  "source": "uuid-of-method-getAccounts",
  "target": "uuid-of-class-List",
  "properties": {
    "method_name": "getAccounts",
    "return_type": "List<Account>",
    "is_collection": true,
    "is_generic": true,
    "generic_arguments": ["Account"]
  }
}
```

For void methods:

```json
{
  "type": "RETURNS",
  "source": "uuid-of-method-updateProfile",
  "target": "uuid-of-void-type",
  "properties": {
    "method_name": "updateProfile",
    "return_type": "void",
    "is_void": true
  }
}
```

## Required Implementation

1. Create `MethodReturnTypeRelationshipBuilder` in `POC/2_Parsers/java_parser/`
2. For each Method entity:
   - Parse the return type declaration
   - Resolve the fully qualified type name
   - Find or create the target type entity
   - Build `RETURNS` relationship
3. Handle generic return types
4. Handle collection return types
5. Handle array return types
6. Handle primitive return types
7. Handle void return type (create singleton Void type entity)

## Validation Checklist

- [ ] Simple type relationship created: returns `String` → `RETURNS` → String
- [ ] Custom type relationship created: returns `AspspSettings` → `RETURNS` → AspspSettings
- [ ] Generic type handled: returns `List<Account>` → `RETURNS` → List
- [ ] Array type handled: returns `String[]` → `RETURNS` → String
- [ ] Primitive type handled: returns `int` → `RETURNS` → int
- [ ] Void type handled: returns `void` → `RETURNS` → void
- [ ] Collection metadata preserved in relationship properties
- [ ] Generic arguments preserved in relationship properties
- [ ] Relationship points to correct target entity UUID

## Testing Requirements

1. Unit test: simple return type relationship
2. Unit test: custom class return type
3. Unit test: generic return type
4. Unit test: array return type
5. Unit test: primitive return type
6. Unit test: void return type
7. Unit test: nested generic return type: `Map<String, List<Account>>`
8. Integration test: all Method entities have RETURNS relationships
9. Integration test: relationships point to valid type entities

## Documentation Updates

Update `POC/2_Parsers/java_parser/README.md`:
- Add RETURNS to relationship list
- Document return type handling
- Document void type handling
- Explain generic return type extraction
