# Markdown Parser: Missing Code Block Entities

## Priority

**Low**

## Goal

Extract code blocks as separate entities with language metadata.

## Current Issue

Code blocks embedded in Markdown specifications are not extracted as entities.

Examples of missing code blocks:
- JSON examples
- HTTP request/response examples
- XML snippets
- Configuration examples

These code blocks are valuable for:
- Understanding data structures
- Extracting example DTOs
- Validating API contracts
- Generating test fixtures

## Expected Behavior

Code blocks should be extracted as `CodeBlock` entities:

```json
{
  "type": "CodeBlock",
  "name": "JSON example in Section 4.2",
  "source": "markdown_parser:nextgenpsd2_implementation_guidelines_1_3:codeblock:245",
  "properties": {
    "language": "json",
    "code": "{\n  \"accountId\": \"12345\",\n  \"currency\": \"EUR\"\n}",
    "line_start": 245,
    "line_end": 249,
    "parent_section": "4.2",
    "caption": null,
    "is_example": true
  }
}
```

For HTTP examples:

```json
{
  "type": "CodeBlock",
  "name": "HTTP request example",
  "source": "markdown_parser:nextgenpsd2_implementation_guidelines_1_3:codeblock:310",
  "properties": {
    "language": "http",
    "code": "POST /v1/payments/sepa-credit-transfers\nContent-Type: application/json\n...",
    "line_start": 310,
    "line_end": 318,
    "parent_section": "4.8.1",
    "is_request": true
  }
}
```

Relationships to create:
- `HAS_CODE_BLOCK` from Section to CodeBlock
- `CONTAINS` from Section to CodeBlock

## Required Implementation

1. Create `CodeBlockExtractor` in `POC/2_Parsers/markdown_parser/`
2. Detect fenced code blocks: triple backticks with optional language
3. Extract code block language tag (```json, ```xml, ```http, etc.)
4. Extract code content
5. Extract code block line range
6. Associate code block with parent section
7. Build CodeBlock entities
8. Build `HAS_CODE_BLOCK` relationships

## Validation Checklist

- [ ] Fenced code blocks detected: ` ```json`
- [ ] Language tag extracted
- [ ] Code content preserved exactly (no formatting changes)
- [ ] Line numbers captured
- [ ] Parent section associated
- [ ] Indented code blocks handled
- [ ] Code blocks without language tags handled
- [ ] `HAS_CODE_BLOCK` relationships created
- [ ] Empty code blocks handled gracefully

## Testing Requirements

1. Unit test: JSON code block extraction
2. Unit test: XML code block extraction
3. Unit test: HTTP code block extraction
4. Unit test: code block without language tag
5. Unit test: multiple code blocks in one section
6. Unit test: code block line number accuracy
7. Integration test: all code blocks extracted from sample specifications
8. Integration test: verify code content is preserved exactly

## Documentation Updates

Update `POC/2_Parsers/markdown_parser/README.md`:
- Add CodeBlock to entity list
- Document HAS_CODE_BLOCK relationship
- Explain language tag extraction
- Document code preservation guarantees
