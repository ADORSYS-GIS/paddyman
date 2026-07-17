# Ticket 006: Extract OpenAPI Tags as First-Class Entities

## Goal

Modify the OpenAPI parser to extract each `tag` from the global `tags` list and from `operations` as a distinct, first-class `Tag` entity.

## Current Issue

Tags are used within operations to group them, but the parser does not create `Tag` entities. The tag names are stored as a simple list of strings in the `tags` attribute of an `Operation` (once operations are extracted as separate entities). This prevents using tags as a formal grouping mechanism in the graph.

## Expected Behavior

The parser must create a dedicated `Tag` entity for each unique tag name defined in the specification. It should then create relationships between `Operations` and the `Tag` entities they reference.

## Required Implementation

1.  Define a new Pydantic model for the `Tag` entity in `shared/models`. It should include `name` and `description`.
2.  Update the `openapi_parser` to first process the global `tags` array in the specification root to create initial `Tag` entities.
3.  When parsing an `Operation`, iterate through its `tags` array.
4.  For each tag string, find the existing `Tag` entity or create a new one if it doesn't exist.
5.  Create a relationship from the `Operation` to the corresponding `Tag` entity.
6.  Preserve provenance and source location for each `Tag` entity, sourcing the location from the global `tags` list where possible.

## Validation

1.  Regenerate the OpenAPI parser outputs.
2.  Inspect the output for a specification that uses tags.
3.  Confirm that a distinct `Tag` entity is created for each unique tag name.
4.  Verify that the `name` and `description` (if provided in the global list) are correctly populated.
5.  Select an operation and confirm that it is linked to the correct `Tag` entities.
6.  Validate that `provenance` and `source_metadata` are present for each `Tag`.

## Acceptance Criteria

- Every unique tag in an OpenAPI specification is parsed into a distinct `Tag` entity.
- `Operations` are correctly linked to the `Tag` entities they use.
- Source location and provenance are preserved for every `Tag` entity.
- The schema for `Tag` entities conforms to the model defined in `shared/models`.

## Testing Requirements

- Add a new unit test to `tests/test_openapi_parser.py` that validates the creation of `Tag` entities and their relationships to `Operations`.
- Ensure all existing tests pass.

## Documentation Updates

- Update `docs/system_design/architectures/architecture_review.md` to include the new `Tag` entity.

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
