# Ticket 008: Verify Markdown Frontmatter Extraction

## Goal

Verify that the Markdown parser correctly extracts YAML frontmatter from `.md` files and represents it as structured metadata or distinct entities in the parsed output.

## Current Issue

The parser is documented to handle frontmatter, but the analysis of the current output files under `POC/DataSource/parsed_output/markdown/` does not provide conclusive evidence of this capability. It is unclear if frontmatter is being parsed at all, and if so, how it is being stored.

## Expected Behavior

The Markdown parser must identify and parse YAML frontmatter blocks at the beginning of Markdown files. The key-value pairs within the frontmatter should be extracted and stored as attributes of the root `Document` entity. For example, `specification_name`, `version`, and `organization` should be directly accessible on the `Document` object.

## Required Implementation

1.  Review the existing `markdown_parser` implementation to determine if frontmatter parsing logic exists.
2.  If it exists, ensure it correctly handles common frontmatter formats and edge cases.
3.  If it does not exist, add a step that uses a library (like `python-frontmatter`) to parse the frontmatter from the document content before processing the Markdown body.
4.  Map the parsed frontmatter data to the corresponding fields in the `Document` entity model from `shared/models`.
5.  Ensure that the frontmatter block is excluded from the rest of the document's text content to avoid it being parsed as a code block or paragraph.

## Validation

1.  Create a sample `.md` file containing a YAML frontmatter block with keys like `specification_name`, `version`, etc.
2.  Run the Markdown parser on this sample file.
3.  Inspect the resulting JSON output.
4.  Confirm that the root `Document` entity contains attributes corresponding to the keys in the frontmatter.
5.  Verify that the frontmatter content does not appear in the parsed `text` or as a separate `CodeBlock` or `Paragraph` entity.
6.  Regenerate all Markdown parser outputs and spot-check several files to ensure the behavior is consistent.

## Acceptance Criteria

- YAML frontmatter in `.md` files is successfully parsed.
- The key-value pairs from the frontmatter are stored as attributes on the root `Document` entity.
- The frontmatter block itself is not present in the parsed body of the document.
- The parser does not fail on documents without frontmatter.
- The schema for the `Document` entity, including the new metadata fields, conforms to the model in `shared/models`.

## Testing Requirements

- Add a new unit test to `tests/test_markdown_parser.py` that uses a sample file with frontmatter and asserts that the metadata is correctly extracted.
- Add another test case for a file without frontmatter to ensure no regressions.
- Ensure all existing tests pass.

## Documentation Updates

- If not already present, update `docs/best_practices.md` to clarify how frontmatter is expected to be used and parsed.

## Completion Criteria

- All validation and acceptance criteria are met.
- Parser outputs are regenerated and reflect the correct frontmatter parsing.
- No regressions are introduced.

## Implementation Loop

1.  Implement the changes.
2.  Regenerate parser outputs.
3.  Compare outputs with expected behavior.
4.  Validate every checklist item.
5.  Identify and address any remaining gaps.
6.  Repeat until all validation items and acceptance criteria pass.
