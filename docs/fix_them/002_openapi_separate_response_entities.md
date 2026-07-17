# Ticket 002: Extract OpenAPI Responses as First-Class Entities

## Goal

Modify the OpenAPI parser to extract each `response` (e.g., `200`, `404`) as a distinct, first-class `Response` entity, linked to its parent `Operation`.

## Current Issue

Currently, responses are not treated as unique entities. The parser generates a `response_match_keys` metadata field within the `Endpoint` object, which is a fingerprint of response schemas. This is insufficient for graph-based analysis, as it prevents direct queries on response properties or relationships to schemas.

## Expected Behavior

The parser must create a dedicated `Response` entity for each status code defined under an operation in the OpenAPI specification. Each `Response` entity should be linked to its parent `Operation` and contain its description and a link to its content schema.

## Required Implementation

1.  Define a new Pydantic model for the `Response` entity in `shared/models`. It should include fields for `status_code`, `description`, and a relationship to its `Schema`.
2.  In the `openapi_parser`, while processing each `Operation`, iterate through the `responses` map.
3.  For each entry (e.g., `"200"`, `"404"`), create an instance of the new `Response` entity.
4.  Populate the entity with the status code and `description`.
5.  Establish a relationship from the `Response` entity to its parent `Operation`.
6.  If the response contains a `content` field, parse the schema and establish a relationship from the `Response` to the corresponding `Schema` or `DTO` entity.
7.  Preserve full provenance and source location metadata for each `Response` entity.

## Validation

1.  Regenerate the OpenAPI parser outputs.
2.  Select an operation from a parsed specification that has multiple defined responses.
3.  Confirm that a distinct `Response` entity is created for each status code (`200`, `401`, `404`, etc.).
4.  Verify that the `status_code` and `description` are correctly populated.
5.  Ensure each `Response` entity is linked to its parent `Operation`.
6.  Check that each `Response` entity correctly links to its `Schema` or `DTO` if a content body is defined.
7.  Validate that `provenance` and `source_metadata` are present and accurate for every `Response`.

## Acceptance Criteria

- Every response in an OpenAPI specification is parsed into a distinct `Response` entity.
- Each `Response` entity contains the `status_code` and `description`.
- Each `Response` entity is correctly linked to its parent `Operation`.
- Each `Response` entity with a body is correctly linked to its `Schema` or `DTO`.
- Source location and provenance are preserved for every `Response` entity.
- The schema for `Response` entities conforms to the model defined in `shared/models`.

## Testing Requirements

- Add a new unit test to `tests/test_openapi_parser.py` that validates the creation of `Response` entities and their relationships to `Operations` and `Schemas`.
- Ensure all existing tests pass.

## Documentation Updates

- Update `docs/system_design/architectures/architecture_review.md` to include the new `Response` entity.

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
