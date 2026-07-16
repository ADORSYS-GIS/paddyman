# Java Parser: Expand Method Call Extraction

## Priority

**High**

## Goal

Extract comprehensive method call information including call site line numbers, arguments, and receiver types.

## Current Issue

Current `CALLS` relationships exist but may lack:
- Call site line numbers (where the call occurs in the caller method)
- Argument count and types
- Receiver object type (for instance method calls)
- Static vs instance call distinction
- Method signature matching

Example current relationship:

```json
{
  "type": "CALLS",
  "source": "AspspProfileConfigurationNotFoundException#AspspProfileConfigurationNotFoundException",
  "target": "String#format",
  "source_method": "AspspProfileConfigurationNotFoundException",
  "target_method": "format",
  "target_class": "String"
}
```

Missing information:
- Where in the source method is this call (line number)?
- How many arguments were passed?
- What is the complete method signature?

## Expected Behavior

Enhanced `CALLS` relationships should include complete call information:

```json
{
  "type": "CALLS",
  "source_entity_id": "uuid-of-source-method",
  "target_entity_id": "uuid-of-target-method",
  "properties": {
    "source_method": "AspspProfileConfigurationNotFoundException",
    "target_method": "format",
    "target_class": "String",
    "call_site_line": 28,
    "is_static": true,
    "receiver_type": "String",
    "argument_count": 2,
    "argument_types": ["String", "Object[]"],
    "method_signature": "format(String, Object[])"
  }
}
```

For instance method calls:

```json
{
  "type": "CALLS",
  "source_entity_id": "uuid-of-source-method",
  "target_entity_id": "uuid-of-target-method",
  "properties": {
    "source_method": "getAccounts",
    "target_method": "findAll",
    "target_class": "AccountRepository",
    "call_site_line": 45,
    "is_static": false,
    "receiver_type": "AccountRepository",
    "receiver_variable": "accountRepository",
    "argument_count": 0,
    "argument_types": [],
    "method_signature": "findAll()"
  }
}
```

## Required Implementation

1. Extend `JavaRelationshipBuilder` to capture detailed call information
2. For each method call detected:
   - Extract call site line number
   - Determine if static or instance call
   - Extract receiver type
   - Count arguments
   - Extract argument types
   - Build complete method signature
3. Store all information in relationship properties
4. Link to actual method entities using UUIDs when possible

## Validation Checklist

- [ ] Call site line number captured
- [ ] Static call detected: `Math.max(a, b)`
- [ ] Instance call detected: `account.getBalance()`
- [ ] Receiver type captured for instance calls
- [ ] Argument count captured
- [ ] Argument types extracted
- [ ] Method signature constructed
- [ ] Chain calls handled: `account.getOwner().getName()`
- [ ] Constructor calls distinguished from method calls
- [ ] Relationships use entity UUIDs (not just string names)

## Testing Requirements

1. Unit test: static method call
2. Unit test: instance method call
3. Unit test: call with no arguments
4. Unit test: call with multiple arguments
5. Unit test: chain method call
6. Unit test: constructor call
7. Unit test: generic method call
8. Integration test: verify call site line numbers are correct
9. Integration test: verify argument counts match actual calls
10. Integration test: verify receiver types are correct

## Documentation Updates

Update `POC/2_Parsers/java_parser/README.md`:
- Document enhanced CALLS relationship properties
- Explain static vs instance call detection
- Document chain call handling
- Provide examples of call site tracking
