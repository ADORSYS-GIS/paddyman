# Java Parser: Missing Spring Bean Dependency Injection Relationships

## Priority

**High**

## Goal

Extract explicit Spring dependency injection relationships from field and constructor injection.

## Current Issue

Current `INJECTS` relationships exist but are generic:

```json
{
  "type": "INJECTS",
  "source": "AspspProfileConfigurationNotFoundException",
  "target": "String",
  "injection_type": "constructor",
  "field_name": null
}
```

This doesn't capture:
- Spring-specific injection mechanisms (@Autowired, @Inject, @Resource)
- Qualifier annotations (@Qualifier, @Named)
- Required vs optional injection
- Primary bean selection
- Bean names
- Injection points for Spring beans

## Expected Behavior

Enhanced dependency injection relationships should distinguish Spring-managed dependencies:

For field injection:

```json
{
  "type": "INJECTS_BEAN",
  "source_entity_id": "uuid-of-class-AccountService",
  "target_entity_id": "uuid-of-class-AccountRepository",
  "properties": {
    "injection_type": "field",
    "field_name": "accountRepository",
    "framework": "spring",
    "annotation": "@Autowired",
    "required": true,
    "qualifier": null,
    "bean_name": null
  }
}
```

For constructor injection with qualifier:

```json
{
  "type": "INJECTS_BEAN",
  "source_entity_id": "uuid-of-class-PaymentService",
  "target_entity_id": "uuid-of-class-PaymentRepository",
  "properties": {
    "injection_type": "constructor",
    "parameter_name": "paymentRepository",
    "parameter_position": 0,
    "framework": "spring",
    "annotation": "@Autowired",
    "required": true,
    "qualifier": "@Qualifier(\"primaryPaymentRepo\")",
    "bean_name": "primaryPaymentRepo"
  }
}
```

For optional injection:

```json
{
  "type": "INJECTS_BEAN",
  "source_entity_id": "uuid-of-class-NotificationService",
  "target_entity_id": "uuid-of-class-EmailClient",
  "properties": {
    "injection_type": "field",
    "field_name": "emailClient",
    "framework": "spring",
    "annotation": "@Autowired",
    "required": false,
    "qualifier": null
  }
}
```

## Required Implementation

1. Create `SpringBeanRelationshipBuilder` in `POC/2_Parsers/java_parser/`
2. Detect Spring injection annotations:
   - `@Autowired`
   - `@Inject` (JSR-330)
   - `@Resource` (JSR-250)
3. Extract injection metadata:
   - Field injection: `@Autowired private AccountRepository repo;`
   - Constructor injection: `@Autowired public Service(AccountRepository repo)`
   - Setter injection: `@Autowired public void setRepo(AccountRepository repo)`
4. Extract qualifier annotations:
   - `@Qualifier("beanName")`
   - `@Named("beanName")`
   - `@Primary`
5. Extract required/optional flag from `@Autowired(required = false)`
6. Build `INJECTS_BEAN` relationships with complete metadata

## Validation Checklist

- [ ] Field injection detected
- [ ] Constructor injection detected
- [ ] Setter injection detected
- [ ] `@Autowired` annotation recognized
- [ ] `@Inject` annotation recognized
- [ ] `@Resource` annotation recognized
- [ ] `@Qualifier` annotation extracted
- [ ] `@Named` annotation extracted
- [ ] `required` attribute captured
- [ ] Bean names extracted from qualifiers
- [ ] Multiple dependencies in constructor handled
- [ ] Optional dependencies marked as `required: false`

## Testing Requirements

1. Unit test: field injection with @Autowired
2. Unit test: constructor injection with @Autowired
3. Unit test: setter injection
4. Unit test: @Qualifier annotation
5. Unit test: @Named annotation
6. Unit test: required = false
7. Unit test: multiple constructor parameters
8. Unit test: @Resource annotation
9. Integration test: all Spring beans have INJECTS_BEAN relationships
10. Integration test: qualifier names match actual bean definitions

## Documentation Updates

Update `POC/2_Parsers/java_parser/README.md`:
- Add INJECTS_BEAN to relationship list
- Document Spring injection detection
- Document qualifier handling
- Provide examples of field, constructor, and setter injection
