# Java Parser: Incomplete Annotation Attributes

## Priority

**High**

## Goal

Extract complete annotation attribute values, not just empty dictionaries.

## Current Issue

Annotation entities currently contain an empty `attributes` dictionary:

```json
{
  "type": "Annotation",
  "name": "@Data",
  "attributes": {},
  "qualified_name": "lombok.Data"
}
```

This loses critical information such as:
- `@RequestMapping(path = "/api/v1", method = RequestMethod.POST)`
- `@Value("${property.name}")`
- `@Autowired(required = false)`
- `@JsonProperty(value = "customName", required = true)`

Without attribute values:
- Dependency injection configuration is incomplete
- API endpoint mappings are missing
- Configuration property bindings are unknown
- Validation rules are lost

## Expected Behavior

Annotation entities should capture all attribute values:

```json
{
  "type": "Annotation",
  "name": "@RequestMapping",
  "qualified_name": "org.springframework.web.bind.annotation.RequestMapping",
  "attributes": {
    "path": "/api/v1/accounts",
    "method": ["RequestMethod.GET", "RequestMethod.POST"],
    "produces": "application/json"
  }
}
```

```json
{
  "type": "Annotation",
  "name": "@Value",
  "qualified_name": "org.springframework.beans.factory.annotation.Value",
  "attributes": {
    "value": "${aspsp.profile.baseUrl}"
  }
}
```

## Required Implementation

1. Extend `AnnotationEntityBuilder` to parse annotation attribute expressions
2. Extract attribute names and values from annotation syntax
3. Handle different value types:
   - String literals: `"value"`
   - Numeric literals: `123`
   - Boolean literals: `true`, `false`
   - Enum references: `RequestMethod.POST`
   - Array values: `{value1, value2}`
   - Nested annotations: `@JsonProperty(...)`
4. Store attribute key-value pairs in `attributes` dictionary
5. Preserve attribute source text when values are complex expressions

## Validation Checklist

- [ ] Simple string attribute extracted: `@Value("${property}")`
- [ ] Numeric attribute extracted: `@Order(1)`
- [ ] Boolean attribute extracted: `@Autowired(required = false)`
- [ ] Enum attribute extracted: `@RequestMapping(method = RequestMethod.POST)`
- [ ] Array attribute extracted: `@RequestMapping(produces = {"json", "xml"})`
- [ ] Multiple attributes extracted: `@JsonProperty(value = "name", required = true)`
- [ ] Default attribute extracted: `@Value("literal")` → `attributes.value`
- [ ] Nested annotations handled gracefully
- [ ] Empty annotations remain valid: `@Override` → `attributes: {}`

## Testing Requirements

1. Unit test: single string attribute
2. Unit test: multiple attributes
3. Unit test: array attributes
4. Unit test: enum attributes
5. Unit test: boolean attributes
6. Unit test: nested annotations
7. Unit test: annotation without attributes
8. Integration test: Spring annotations (@RequestMapping, @Autowired, @Value)
9. Integration test: Lombok annotations (@Data, @Builder)
10. Integration test: validation annotations (@NotNull, @Size)

## Documentation Updates

Update `POC/2_Parsers/java_parser/README.md`:
- Document annotation attribute extraction
- Provide examples of common Spring annotations
- Explain attribute type handling
- Note limitations for complex expressions
