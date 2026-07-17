# Ticket 007: Create a Top-Level API Entity for Each OpenAPI Specification

## Goal

Modify the OpenAPI parser to create a single, top-level `API` entity for each OpenAPI specification file it parses. This entity will serve as the root node for all other entities extracted from that file.

## Current Issue

The parser currently produces a flat list of entities (Endpoints, Schemas, etc.) for each specification. There is no single root entity that represents the API specification itself. This makes it difficult to query or traverse all components belonging to a single API and to distinguish between different APIs in the graph.

## Expected Behavior

For each OpenAPI specification file, the parser must generate exactly one `API` entity. This entity should contain the high-level information from the `info` block (title, version, description) and serve as a parent to all `Endpoints`, `Schemas`, `SecuritySchemes`, and other top-level components from that file.

## Required Implementation

1.  Define a new Pydantic model for the `API` entity in `shared/models`. It should include fields for `title`, `version`, and `description`.
2.  At the beginning of the parsing process for a new file, create an instance of the `API` entity.
3.  Populate it with the data from the `info` object in the specification.
4.  As other entities (`Endpoint`, `Schema`, etc.) are created, establish a relationship from the `API` entity to them.
5.  The final output for a single specification file should be a single JSON object with the `API` entity at the root, containing lists of its child entities.
6.  Preserve full provenance and source location metadata for the `API` entity, pointing to the root of the specification file.

## Validation

1.  Regenerate the OpenAPI parser outputs.
2.  Inspect the JSON output for any parsed specification.
3.  Confirm that the root of the JSON object is a single `API` entity.
4.  Verify that the `title`, `version`, and `description` from the spec's `info` block are correctly populated in the `API` entity.
5.  Ensure that all `Endpoints`, `Schemas`, and other entities from that file are linked from the `API` entity.
6.  Validate that the `provenance` and `source_metadata` for the `API` entity are present and point to the specification file itself.

## Acceptance Criteria

- Each parsed OpenAPI specification produces exactly one top-level `API` entity.
- The `API` entity correctly captures the `title`, `version`, and `description` from the `info` block.
- All other entities extracted from the specification are children of or linked from the `API` entity.
- Source location and provenance are preserved for the `API` entity.
- The schema for the `API` entity conforms to the model defined in `shared/models`.

## Testing Requirements

- Modify existing tests in `tests/test_openapi_parser.py` to assert that the output is a single `API` entity.
- Add tests to validate the content of the `API` entity and its relationships to child objects.
- Ensure all tests pass.

## Documentation Updates

- Update `docs/system_design/architectures/architecture_review.md` to show the `API` entity as the root for OpenAPI-derived graphs.

## Completion Criteria

- All validation and acceptance criteria are met.
- Parser outputs are regenerated and reflect the new structure.
- No regressions are introduced.

## Implementation Loop

1.  Implement the changes.
2.  Regenerate parser outputs.
3.  Compare outputs with expected behavior.
4.  Validate every checklist item.
5.  Identify and address any remaining gaps.
6.  Repeat until all validation items and acceptance criteria pass.
