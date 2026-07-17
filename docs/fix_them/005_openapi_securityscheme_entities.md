# Ticket 005: Extract OpenAPI Security Schemes as First-Class Entities

## Goal

Modify the OpenAPI parser to extract each security scheme from the `components/securitySchemes` section as a distinct, first-class `SecurityScheme` entity.

## Current Issue

Security schemes are identified by the parser but are only stored in the `security` metadata field of the `Endpoint` object. They are not created as separate entities, which prevents analyzing security requirements across the API or linking operations to the specific schemes they use.

## Expected Behavior

The parser must create a dedicated `SecurityScheme` entity for each scheme defined in `components/securitySchemes`. Additionally, it should create relationships between `Operations` and the `SecurityScheme` entities they reference.

## Required Implementation

1.  Define a new Pydantic model for the `SecurityScheme` entity in `shared/models`. It should include fields for `scheme_name`, `type` (e.g., "oauth2", "http"), `description`, and other relevant details like `flows` for OAuth2.
2.  Update the `openapi_parser` to process the `components/securitySchemes` object.
3.  For each entry, create an instance of the new `SecurityScheme` entity and populate it with the corresponding data.
4.  When parsing an `Operation`, inspect its `security` requirement.
5.  For each security requirement listed, create a relationship from the `Operation` to the corresponding `SecurityScheme` entity.
6.  Preserve full provenance and source location metadata for each `SecurityScheme` entity.

## Validation

1.  Regenerate the OpenAPI parser outputs.
2.  Inspect the output for a specification that defines multiple security schemes.
3.  Confirm that a distinct `SecurityScheme` entity is created for each one (e.g., "petstore_auth", "api_key").
4.  Verify that the entity's attributes (`type`, `flows`, etc.) are correctly populated.
5.  Select an operation that uses a security scheme and confirm that a relationship is created between the `Operation` and the `SecurityScheme`.
6.  Validate that `provenance` and `source_metadata` are present and accurate for every `SecurityScheme`.

## Acceptance Criteria

- Every security scheme in an OpenAPI specification is parsed into a distinct `SecurityScheme` entity.
- Each `SecurityScheme` entity correctly models its type, flows, and other properties.
- `Operations` are correctly linked to the `SecurityScheme` entities they use.
- Source location and provenance are preserved for every `SecurityScheme` entity.
- The schema for `SecurityScheme` entities conforms to the model defined in `shared/models`.

## Testing Requirements

- Add a new unit test to `tests/test_openapi_parser.py` that validates the creation of `SecurityScheme` entities and their relationships to `Operations`.
- Ensure all existing tests pass.

## Documentation Updates

- Update `docs/system_design/architectures/architecture_review.md` to include the new `SecurityScheme` entity.

## Completion Criteria

- All validation and acceptance criteria are met.
- Parser outputs are regenerated and reflect the new behavior.
- No regressions are introduced.

## Implementation Loop

1.  Implement the changes.
2.  Regenerate parser outputs.
3.  Compare outputs with expected behavior.
4.  Validate every checklist item.
5.  Identify and address any remaining gaps.
6.  Repeat until all validation items and acceptance criteria pass.
