# Ticket 003: Extract OpenAPI Request Bodies as First-Class Entities

## Goal

Modify the OpenAPI parser to extract each `requestBody` as a distinct, first-class `RequestBody` entity, linked to its parent `Operation`.

## Current Issue

The parser currently identifies request bodies but only stores a reference in the `request_body_ref` metadata field of the `Endpoint` object. It does not create a separate `RequestBody` entity. This prevents modeling the request body's content, media types, and schema as a distinct node in the graph.

## Expected Behavior

The parser must create a dedicated `RequestBody` entity for each `requestBody` defined under an operation. This entity should be linked to its parent `Operation` and contain details about its content types and associated schemas.

## Required Implementation

1.  Define a new Pydantic model for the `RequestBody` entity in `shared/models`. It should include fields for `description`, `required`, and a dictionary or list to hold `content` types and their associated `Schema` relationships.
2.  In the `openapi_parser`, when processing an `Operation` that has a `requestBody`, create an instance of the new `RequestBody` entity.
3.  Populate the entity with the `description` and `required` status.
4.  Iterate through the `content` map (e.g., `application/json`). For each media type, establish a relationship to the corresponding `Schema` or `DTO` entity.
5.  Establish a relationship from the `RequestBody` entity to its parent `Operation`.
6.  Preserve full provenance and source location metadata for each `RequestBody` entity.

## Validation

1.  Regenerate the OpenAPI parser outputs.
2.  Select an operation from a parsed specification that has a `requestBody`.
3.  Confirm that a `RequestBody` entity is created and linked to the `Operation`.
4.  Verify that the `description` and `required` fields are correctly populated.
5.  Check that the `content` map is parsed correctly, with media types linking to the appropriate `Schema` or `DTO`.
6.  Validate that `provenance` and `source_metadata` are present and accurate for the `RequestBody` entity.

## Acceptance Criteria

- Every `requestBody` in an OpenAPI specification is parsed into a distinct `RequestBody` entity.
- Each `RequestBody` entity is correctly linked to its parent `Operation`.
- The `content` of the `RequestBody`, including media types and schemas, is correctly modeled.
- Source location and provenance are preserved for every `RequestBody` entity.
- The schema for `RequestBody` entities conforms to the model defined in `shared/models`.

## Testing Requirements

- Add a new unit test to `tests/test_openapi_parser.py` that validates the creation of `RequestBody` entities and their relationships.
- Ensure all existing tests pass.

## Documentation Updates

- Update `docs/system_design/architectures/architecture_review.md` to include the new `RequestBody` entity.

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
