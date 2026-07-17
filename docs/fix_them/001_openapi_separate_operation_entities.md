# Ticket 001: Extract OpenAPI Operations as First-Class Entities

## Goal

Modify the OpenAPI parser to extract each `operation` (e.g., `get`, `post`) as a distinct, first-class `Operation` entity, instead of embedding it within the `Endpoint` entity.

## Current Issue

The OpenAPI parser currently processes operations as part of the `Endpoint` object. The operation's details (`operationId`, `summary`, `tags`, etc.) are stored as attributes of the `Endpoint`. This approach prevents treating operations as unique nodes in the graph, limiting the ability to form direct relationships with other entities like `Parameters` and `Responses`.

## Expected Behavior

The parser must produce a dedicated `Operation` entity for each HTTP method defined under a path in the OpenAPI specification. Each `Operation` entity should be linked to its parent `Endpoint` and contain all relevant details.

## Required Implementation

1.  Define a new Pydantic model for the `Operation` entity in `shared/models`. It should include fields for `operation_id`, `summary`, `description`, `tags`, and relationships to `Parameters`, `RequestBodies`, and `Responses`.
2.  Update the `openapi_parser` to iterate through each path's HTTP methods (`get`, `put`, `post`, `delete`, etc.).
3.  For each method, create an instance of the new `Operation` entity.
4.  Populate the entity with the `operationId`, `summary`, `description`, and `tags` from the specification.
5.  Establish a relationship linking the `Operation` entity back to its parent `Endpoint` entity.
6.  Preserve full provenance and source location metadata for each `Operation` entity.

## Validation

1.  Regenerate the OpenAPI parser outputs.
2.  Inspect the JSON output for a representative OpenAPI specification.
3.  Confirm that for each path with a `get`, `post`, etc., a corresponding `Operation` entity is created.
4.  Verify that the `operation_id`, `summary`, and `tags` are correctly populated.
5.  Ensure each `Operation` entity has a valid relationship to its parent `Endpoint`.
6.  Check that `provenance` and `source_metadata` (including line numbers) are present and accurate for every `Operation`.

## Acceptance Criteria

- Every operation in an OpenAPI specification is parsed into a distinct `Operation` entity.
- Each `Operation` entity contains the `operationId`, `summary`, `description`, and `tags`.
- Each `Operation` entity is correctly linked to its parent `Endpoint`.
- Source location and provenance are preserved for every `Operation` entity.
- The schema for `Operation` entities conforms to the model defined in `shared/models`.

## Testing Requirements

- Add a new unit test to `tests/test_openapi_parser.py` that specifically validates the creation and content of `Operation` entities from a sample OpenAPI file.
- Ensure all existing tests continue to pass.

## Documentation Updates

- Update `docs/system_design/architectures/architecture_review.md` to reflect the new `Operation` entity and its relationships.

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
