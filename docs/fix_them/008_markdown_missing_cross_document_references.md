# Markdown Parser: Missing Cross-Document Reference Entities

## Priority

**Medium**

## Goal

Extract cross-document references as explicit entities and relationships.

## Current Issue

The Markdown parser captures document structure (headings, sections, paragraphs, tables, lists) but does not extract cross-document references.

Examples of missing references:
- `See Section 4.2 for details`
- `As defined in the Implementation Guidelines 1.3`
- `Refer to [PSD2] article 66`
- `[NextGenPSD2]` specification references

These references are critical for:
- Understanding document dependencies
- Tracing specification requirements
- Building a knowledge graph of related specifications
- Detecting broken or outdated references

## Expected Behavior

Cross-document references should be extracted as `Reference` entities:

```json
{
  "type": "Reference",
  "name": "Section 4.2 reference",
  "source": "markdown_parser:nextgenpsd2_implementation_guidelines_1_3:paragraph:125",
  "properties": {
    "reference_text": "See Section 4.2",
    "reference_type": "section",
    "target_section": "4.2",
    "target_document": null,
    "context": "See Section 4.2 for details on OAuth2 authentication",
    "line_number": 125
  }
}
```

For external specification references:

```json
{
  "type": "Reference",
  "name": "[PSD2] article 66 reference",
  "source": "markdown_parser:nextgenpsd2_implementation_guidelines_1_3:paragraph:42",
  "properties": {
    "reference_text": "[PSD2]",
    "reference_type": "external_spec",
    "target_spec": "PSD2",
    "target_article": "66",
    "context": "as defined by article 66 of [PSD2]",
    "line_number": 42
  }
}
```

Relationships to create:
- `REFERENCES` from Paragraph/Section to Reference
- `REFERENCES` from Reference to target Section (if internal)
- `REFERENCES_EXTERNAL` from Reference to external spec name

## Required Implementation

1. Create `ReferenceExtractor` in `POC/2_Parsers/markdown_parser/`
2. Detect reference patterns:
   - Section references: `Section 4.2`, `§4.2`, `Chapter 3`
   - Citation references: `[PSD2]`, `[ISO20022]`, `[RFC6749]`
   - Article references: `article 66`, `Art. 66`
   - Hyperlinks: `[link text](url)`
3. Extract reference context (surrounding text)
4. Build Reference entities with metadata
5. Build `REFERENCES` relationships
6. Resolve internal section references
7. Tag external specification references

## Validation Checklist

- [ ] Section references extracted: `Section 4.2`
- [ ] Citation references extracted: `[PSD2]`
- [ ] Article references extracted: `article 66`
- [ ] Hyperlinks extracted
- [ ] Reference context captured
- [ ] Line numbers preserved
- [ ] `REFERENCES` relationships created
- [ ] Internal references resolved to target sections
- [ ] External references tagged appropriately
- [ ] Markdown links captured: `[text](url)`

## Testing Requirements

1. Unit test: section reference extraction
2. Unit test: citation reference extraction
3. Unit test: article reference extraction
4. Unit test: hyperlink extraction
5. Unit test: multiple references in one paragraph
6. Unit test: internal section resolution
7. Integration test: all specification documents have Reference entities
8. Integration test: verify reference counts match manual inspection

## Documentation Updates

Update `POC/2_Parsers/markdown_parser/README.md`:
- Add Reference to entity list
- Document REFERENCES relationship
- Explain reference pattern matching
- Document external specification tagging
