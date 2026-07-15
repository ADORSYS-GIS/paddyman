Markdown Parser
===============

Purpose
-------

Parses complete Markdown specification files and extracts document structure for downstream extraction stages.

Pipeline Stages
---------------

- Document ingestion — `reader.load_documents` (reads complete .md files)
- Structure extraction — `structure.extract_structure_from_documents` (extracts headings, sections, links, tables, lists)

Input Location
--------------

The pipeline reads complete Markdown specification files from:

`shared.config.settings.markdown_spec_dir`

Default: `POC/DataSource/berlin_group_specification_md_files/`

Specification Metadata Extraction
----------------------------------

The parser automatically extracts specification boundary metadata using a hierarchical fallback strategy:

### Extraction Hierarchy

1. **YAML Frontmatter** (highest priority)
2. **Filename patterns**
3. **Content analysis**
4. **Default values** (lowest priority)

### Frontmatter Format

Markdown files can include YAML frontmatter to explicitly declare metadata:

```markdown
---
title: NextGenPSD2 Implementation Guidelines
version: 1.3
category: Implementation Guidelines
organization: Berlin Group
published: 2021-03-15
---

# Document Content
```

### Filename Patterns

When frontmatter is unavailable, the parser extracts metadata from filenames:

Examples:
- `nextgenpsd2_implementation_guidelines_1_3_clean.md`
  - specification_name: "Nextgenpsd2 Implementation Guidelines"
  - specification_version: "1.3"

- `ais_for_savings_accounts_v1_2.md`
  - specification_name: "AIS For Savings Accounts"
  - specification_version: "1.2"

### Content Analysis

As a fallback, the parser extracts:
- Title from first level-1 heading (`# Title`)
- Version from content (e.g., "Version: 1.3")
- Organization from known patterns (e.g., "by Berlin Group")
- Publication date from date patterns

### Extracted Fields

Each parsed document includes:

- `specification_name` — Name of the specification
- `specification_version` — Version string (e.g., "1.3")
- `specification_category` — Category (e.g., "Implementation Guidelines")
- `source_organization` — Issuing organization (e.g., "Berlin Group")
- `publication_date` — Publication date if available
- `file_path` — Absolute file path
- `relative_path` — Path relative to input directory
- `source_parser` — Always "markdown_parser"
- `parsed_at` — ISO 8601 timestamp

These fields are included in:
- Document entity properties
- `source_metadata` arrays
- `NormalizedDocument` metadata

Document Flow
-------------

```
PDF → Docling → Clean Markdown → POC/DataSource/berlin_group_specification_md_files/ → Markdown Parser
```

Each specification file is processed as a single complete document.

How to run
----------

Normal pipeline execution uses the single parser runner:

```bash
cd POC
PYTHONPATH=.:2_Parsers python3 2_Parsers/parser_pipeline.py
```

This runs Java, OpenAPI, and Markdown parsing and writes the normalized JSON contract for extraction.

For isolated parser tests or debugging:

```bash
cd POC
python -m markdown_parser.main
```

Or call `run_pipeline()` programmatically:

```py
from markdown_parser.main import run_pipeline
summary = run_pipeline()
```

Output Summary
--------------

The entry point prints and returns a JSON summary containing:

- `documents_loaded` — number of complete specification files processed
- `sections_extracted` — total sections found across all documents
- `headings_found` — total headings extracted
- `references_found` — total references (inline links, definitions, citations)
- `tables_found` — total tables extracted
- `errors` — list of any stage errors encountered

Entity Types
------------

The parser extracts the following entity types:

### Document Entity

Represents the complete markdown file.

Properties:
- `file_path` — absolute path to source file
- `specification_name` — extracted specification name
- `specification_version` — extracted version
- `specification_category` — document category
- `source_organization` — issuing organization
- `publication_date` — publication date if available

### Heading Entity

Represents markdown headings (# through ######).

Properties:
- `text` — heading text without markdown syntax
- `level` — heading level (1-6)
- `start_line` — line number in source file
- `markdown_syntax` — original markdown (e.g., "## Introduction")
- `file_path` — source file name
- `slug` — URL-friendly slug (e.g., "api-overview-v1-3")

Example:
```json
{
  "type": "Heading",
  "name": "API Overview: V1.3",
  "properties": {
    "text": "API Overview: V1.3",
    "level": 2,
    "start_line": 15,
    "markdown_syntax": "## API Overview: V1.3",
    "file_path": "spec.md",
    "slug": "api-overview-v1-3"
  }
}
```

### Frontmatter Entity

Represents YAML frontmatter blocks (if present).

Properties:
- `raw_yaml` — original YAML text
- `parsed_fields` — dictionary of parsed YAML key-value pairs
- `file_path` — source file name
- `start_line` — starting line number (typically 1)
- `end_line` — ending line number

Example:
```json
{
  "type": "Frontmatter",
  "name": "Document Frontmatter",
  "properties": {
    "raw_yaml": "title: My Document\nversion: 1.0",
    "parsed_fields": {
      "title": "My Document",
      "version": "1.0"
    },
    "file_path": "spec.md",
    "start_line": 1,
    "end_line": 4
  }
}
```

### Section Entity

Represents logical document sections.

Properties:
- `section_title` — section heading text
- `start_line` — starting line number
- `end_line` — ending line number
- `level` — heading level (1-6)
- `depth` — nesting depth (0 for top-level sections)
- `path` — ancestor path (e.g., "Introduction / Overview")
- `parent_section_id` — ID of parent section (if any)

### Table Entity

Represents markdown tables.

Properties:
- `headers` — list of column headers
- `row_count` — number of data rows (excluding header)
- `column_count` — number of columns
- `caption` — table caption if present (text immediately before table)
- `start_line` — starting line number
- `end_line` — ending line number
- `file_path` — source file name
- `rows_preview` — first three rows of data (for debugging and preview)
- `alignment` — list of column alignments ("left", "center", "right")
- `table_id` — unique table identifier

Example:
```json
{
  "type": "Table",
  "name": "API Endpoints Summary",
  "properties": {
    "headers": ["Method", "Endpoint", "Description"],
    "row_count": 5,
    "column_count": 3,
    "caption": "API Endpoints Summary",
    "start_line": 45,
    "end_line": 51,
    "file_path": "spec.md",
    "rows_preview": [
      ["GET", "/accounts", "List accounts"],
      ["POST", "/payments", "Create payment"],
      ["GET", "/balances", "Get balances"]
    ],
    "alignment": ["left", "left", "left"]
  }
}
```

### List Entity

Represents ordered and unordered lists with full nesting support.

Properties:
- `list_type` — "ordered" or "unordered"
- `item_count` — number of top-level items
- `total_item_count` — total items including nested lists
- `start_line` — starting line number
- `end_line` — ending line number
- `file_path` — source file name
- `is_nested` — boolean indicating if list is nested within another
- `nesting_level` — depth of nesting (0 for top-level)
- `items_preview` — first three items (for debugging and preview)
- `ordered_start` — starting number for ordered lists (default 1)
- `list_id` — unique list identifier

#### List Types

**Unordered List** — Bullet lists using -, *, or +:
```markdown
- Item 1
- Item 2
  - Nested item 2.1
  - Nested item 2.2
- Item 3
```

**Ordered List** — Numbered lists using digits:
```markdown
1. First item
2. Second item
   1. Nested item 2.1
   2. Nested item 2.2
3. Third item
```

**Task List** — GitHub Flavored Markdown task lists:
```markdown
- [ ] Incomplete task
- [x] Completed task
```

#### Nesting Detection

Lists track their nesting relationships:
- `nesting_level`: 0 for top-level, 1 for first nested level, etc.
- `is_nested`: True if list is nested within a parent list
- `item_count`: Only top-level items at this list's level
- `total_item_count`: All items including nested sublists

Example:
```json
{
  "type": "List",
  "name": "Unordered list at line 25",
  "properties": {
    "list_type": "unordered",
    "item_count": 3,
    "total_item_count": 5,
    "start_line": 25,
    "end_line": 30,
    "file_path": "spec.md",
    "is_nested": false,
    "nesting_level": 0,
    "items_preview": [
      "Item 1",
      "Item 2",
      "Item 3"
    ],
    "ordered_start": null
  }
}
```

### Paragraph Entity

Represents text paragraphs.

Properties:
- `text` — paragraph content
- `start_line` — starting line number
- `word_count` — number of words

### CodeBlock Entity

Represents fenced code blocks.

Properties:
- `language` — code language identifier
- `code` — code content
- `start_line` — starting line number

### Reference Entity

Represents markdown references including links, images, autolinks, and footnotes.

Properties:
- `ref_type` — type of reference: "link", "image", "reference_definition", "autolink", "footnote"
- `target_url` — URL or path being referenced
- `anchor_text` — link text (for links)
- `alt_text` — alt text (for images)
- `title` — title attribute if present
- `is_external` — boolean: true for external URLs (http://, https://, etc.)
- `is_relative` — boolean: true for relative paths (../docs/file.md)
- `is_anchor` — boolean: true for internal anchors (#section)
- `target_document` — path to target markdown file (for cross-document references)
- `footnote_label` — label for footnotes (e.g., "1", "note")
- `footnote_content` — content of footnote definition
- `start_line` — line number
- `file_path` — source file name

#### Reference Types

**Link** — Inline markdown link:
```markdown
[Berlin Group](https://www.berlin-group.org "Official Site")
```
Properties:
- `ref_type`: "link"
- `anchor_text`: "Berlin Group"
- `target_url`: "https://www.berlin-group.org"
- `title`: "Official Site"
- `is_external`: true

**Image** — Image reference:
```markdown
![Architecture Diagram](./images/arch.png "System Architecture")
```
Properties:
- `ref_type`: "image"
- `alt_text`: "Architecture Diagram"
- `target_url`: "./images/arch.png"
- `title`: "System Architecture"
- `is_relative`: true

**Reference Definition** — Reference-style link definition:
```markdown
[XS2A]: https://berlin-group.org/xs2a "XS2A Standard"
```
Properties:
- `ref_type`: "reference_definition"
- `anchor_text`: "XS2A"
- `target_url`: "https://berlin-group.org/xs2a"
- `title`: "XS2A Standard"
- `is_external`: true

**Autolink** — URL in angle brackets:
```markdown
<https://www.berlin-group.org>
<mailto:support@example.com>
```
Properties:
- `ref_type`: "autolink"
- `target_url`: "https://www.berlin-group.org"
- `is_external`: true

**Footnote** — Footnote reference:
```markdown
This follows PSD2 standards[^1].

[^1]: Payment Services Directive 2
```
Properties:
- `ref_type`: "footnote"
- `footnote_label`: "1"
- `footnote_content`: "Payment Services Directive 2"

#### URL Classification

References are automatically classified:

- **External URLs**: `https://`, `http://`, `ftp://`, `mailto:`, `tel:`
- **Relative paths**: `../docs/file.md`, `./images/logo.png`, `subfolder/doc.md`
- **Anchors**: `#section-heading`
- **Cross-document**: Links to other `.md` files in the corpus

Example:
```json
{
  "type": "Reference",
  "name": "API Documentation",
  "properties": {
    "ref_type": "link",
    "target_url": "../api/endpoints.md#authentication",
    "anchor_text": "API Documentation",
    "is_external": false,
    "is_relative": true,
    "is_anchor": false,
    "target_document": "../api/endpoints.md",
    "start_line": 42,
    "file_path": "overview.md"
  }
}
```


Relationships
-------------

The parser creates the following relationships:

### CONTAINS (Document → Entity)

Links the document to all its contained entities (sections, headings, tables, etc.).

### TITLED_BY (Section → Heading)

Links each section to its heading.

### NEXT_HEADING (Heading → Heading)

Links headings in sequential document order, enabling document navigation.

Example:
```
Heading(level=1, line=1) → NEXT_HEADING → Heading(level=2, line=5)
Heading(level=2, line=5) → NEXT_HEADING → Heading(level=3, line=10)
```

### HAS_FRONTMATTER (Document → Frontmatter)

Links the document to its frontmatter entity (if present).

### PARENT_SECTION (Section → Section)

Links child sections to their parent sections based on heading hierarchy.

Example:
```
Section(level=2) → PARENT_SECTION → Section(level=1)
Section(level=3) → PARENT_SECTION → Section(level=2)
```

Properties:
- `relationship_type` — "section_hierarchy"
- `child_level` — heading level of child section
- `parent_level` — heading level of parent section

### NEXT_SIBLING (Section → Section)

Links sibling sections at the same hierarchical level in document order.

Example:
```markdown
# Introduction          <- Section 1 (level 1)
## Overview             <- Section 1.1 (level 2)
## Details              <- Section 1.2 (level 2, sibling of 1.1)
# Conclusion            <- Section 2 (level 1, sibling of Section 1)
```

Relationships:
```
Section(1.1) → NEXT_SIBLING → Section(1.2)
Section(1) → NEXT_SIBLING → Section(2)
```

Properties:
- `relationship_type` — "section_sibling"

### FIRST_CHILD (Section → Section)

Links parent sections to their first child section.

Example:
```markdown
# Main Section          <- Parent
## First Subsection     <- First child
## Second Subsection    <- Second child
```

Relationship:
```
Section(Main) → FIRST_CHILD → Section(First Subsection)
```

Properties:
- `relationship_type` — "section_first_child"

### SECTION_CONTENT (Section → Content Entity)

Links sections to their content entities (tables, lists, paragraphs, code blocks).

Also known as:
- `HAS_TABLE` (Section → Table)
- `HAS_LIST` (Section → List)
- `HAS_PARAGRAPH` (Section → Paragraph)
- `HAS_CODE` (Section → CodeBlock)

### NEXT_TABLE (Table → Table)

Links tables in sequential document order, enabling table navigation.

Example:
```
Table(line=10) → NEXT_TABLE → Table(line=25)
Table(line=25) → NEXT_TABLE → Table(line=40)
```

Properties:
- `relationship_type` — "table_sequence"
- `current_line` — start line of source table
- `next_line` — start line of target table

### NEXT_LIST (List → List)

Links top-level lists in sequential document order, enabling list navigation.

Example:
```
List(line=10) → NEXT_LIST → List(line=25)
List(line=25) → NEXT_LIST → List(line=40)
```

Properties:
- `relationship_type` — "list_sequence"

Only applies to top-level lists (nesting_level = 0). Nested lists are tracked separately via NESTED_IN.

### NESTED_IN (List → List)

Links nested lists to their parent lists, establishing the list hierarchy.

Example:
```
List(nesting_level=1, line=12) → NESTED_IN → List(nesting_level=0, line=10)
List(nesting_level=2, line=15) → NESTED_IN → List(nesting_level=1, line=12)
```

Properties:
- `relationship_type` — "list_nesting"
- `nesting_level` — Nesting level of the child list

This enables:
- List hierarchy analysis
- Nested structure navigation
- Content organization queries

### REFERENCES (Container → Reference)

Links sections and paragraphs to references they contain.

Example:
```
Section(line=10) → REFERENCES → Reference(line=15)
Paragraph(line=14) → REFERENCES → Reference(line=15)
```

Properties:
- `relationship_type` — "section_to_reference" or "paragraph_to_reference"

### LINKS_TO (Reference → Section)

Links anchor references to their target sections.

Example:
```
Reference(target_url="#api-overview") → LINKS_TO → Section(heading_anchor="api-overview")
```

Properties:
- `relationship_type` — "reference_to_section"

This enables:
- Link validation
- Cross-reference tracking
- Table of contents generation
- Dead link detection

### NEXT_REFERENCE (Reference → Reference)

Links references in sequential document order.

Example:
```
Reference(line=10) → NEXT_REFERENCE → Reference(line=15)
Reference(line=15) → NEXT_REFERENCE → Reference(line=22)
```

Properties:
- `relationship_type` — "sequential"

Enables reference traversal and analysis.

### FOUND_IN (Reference → Paragraph)

**Note**: This relationship type is deprecated in favor of REFERENCES.

Links references to the paragraphs containing them.

Reference Extraction Modules
-----------------------------

Reference extraction is organized into focused modules:

### Core Modules

**`reference_classifiers.py`** — URL classification functions:
- `is_external_url()` — Detects external URLs
- `is_relative_path()` — Detects relative file paths
- `is_anchor()` — Detects internal anchors
- `is_cross_document()` — Detects cross-document references

**`reference_url_utils.py`** — URL parsing utilities:
- `extract_target_document()` — Extracts target document path
- `extract_anchor_from_url()` — Extracts anchor fragment

### Extraction Modules

**`reference_link_extractors.py`** — Link extraction:
- `extract_inline_links()` — Inline links with title and classification
- `extract_reference_definitions()` — Reference-style link definitions

**`reference_image_extractors.py`** — Image extraction:
- `extract_images()` — Image references with alt text and title

**`reference_advanced_extractors.py`** — Advanced references:
- `extract_autolinks()` — Autolinks (`<https://example.com>`)
- `extract_footnotes()` — Footnote references and definitions

**`reference_extractors.py`** — Unified API:
- Re-exports all extraction functions for backward compatibility

**`reference_entity_builder.py`** — Entity creation:
- `create_reference_entities()` — Orchestrates all extractors

**`reference_relationship_builder.py`** — Relationship creation:
- `create_reference_relationships()` — Creates REFERENCES, LINKS_TO, NEXT_REFERENCE

### Supported Reference Formats

**Inline links:**
```markdown
[Link text](https://example.com "Title")
[Relative link](../docs/file.md)
[Anchor link](#section)
```

**Reference-style links:**
```markdown
[Link text][ref-id]
[ref-id]: https://example.com "Title"
```

**Images:**
```markdown
![Alt text](image.png "Title")
```

**Autolinks:**
```markdown
<https://example.com>
<mailto:user@example.com>
```

**Footnotes:**
```markdown
Text with footnote[^1]
[^1]: Footnote content
```

Testing
-------

Run reference extraction tests:

```bash
cd POC
python -m pytest 2_Parsers/markdown_parser/tests/test_reference_*.py -v
```

Test coverage includes:
- URL classification (external, relative, anchor, cross-document)
- Title attribute extraction
- Image alt text extraction
- Autolink extraction
- Footnote extraction with definitions
- Reference relationships (REFERENCES, LINKS_TO, NEXT_REFERENCE)
- Edge cases and error handling

All modules follow the 150 LOC limit for maintainability.


