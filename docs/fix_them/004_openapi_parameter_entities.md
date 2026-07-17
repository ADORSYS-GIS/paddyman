# Ticket 004: Extract OpenAPI Parameters as First-Class Entities

## Goal

Modify the OpenAPI parser to extract each `parameter` (defined at the path or operation level) as a distinct, first-class `Parameter` entity.

## Current Issue

Parameters are currently parsed and stored in a `parameters` array within the `Endpoint` entity's metadata. They are not treated as unique entities, which prevents linking them directly to the `Operations` they belong to or analyzing them as individual nodes in the graph.

## Expected Behavior

The parser must create a dedicated `Parameter` entity for every parameter defined in an OpenAPI specification. Each `Parameter` entity should be linked to the `Operation` (or `Endpoint` if defined at the path level) it belongs to and contain all its attributes (`name`, `in`, `description`, `required`, `schema`).

## Required Implementation

1.  Define a new Pydantic model for the `Parameter` entity in `shared/models`. It should include fields for `name`, `in` (location, e.g., "query", "header"), `description`, `required`, and a relationship to its `Schema`.
2.  Update the `openapi_parser` to process the `parameters` array at both the path and operation levels.
3.  For each parameter definition, create an instance of the new `Parameter` entity.
4.  Populate the entity with its `name`, `in`, `description`, `required` status, and a link to its `schema`.
5.  Establish a relationship linking the `Parameter` entity to its parent `Operation` or `Endpoint`.
6.  Preserve full provenance and source location metadata for each `Parameter` entity.

## Validation

1.  Regenerate the OpenAPI parser outputs.
2.  Select an operation with several parameters (e.g., path, query, header).
3.  Confirm that a distinct `Parameter` entity is created for each one.
4.  Verify that all attributes (`name`, `in`, `description`, `required`, `schema`) are correctly populated.
5.  Ensure each `Parameter` entity is correctly linked to its parent `Operation` or `Endpoint`.
6.  Validate that `provenance` and `source_metadata` are present and accurate for every `Parameter`.

## Acceptance Criteria

- Every parameter in an OpenAPI specification is parsed into a distinct `Parameter` entity.
- Each `Parameter` entity contains its `name`, `in`, `description`, `required` status, and a link to its `schema`.
- Each `Parameter` entity is correctly linked to its parent `Operation` or `Endpoint`.
- Source location and provenance are preserved for every `Parameter` entity.
- The schema for `Parameter` entities conforms to the model defined in `shared/models`.

## Testing Requirements

- Add a new unit test to `tests/test_openapi_parser.py` that validates the creation of `Parameter` entities from both path and operation-level definitions.
- Ensure all existing tests pass.

## Documentation Updates

- Update `docs/system_design/architectures/architecture_review.md` to include the new `Parameter` entity.

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
