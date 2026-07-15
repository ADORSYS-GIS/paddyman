# Java Parser

## What it does

This component reads Java source code from the configured repositories and automatically extracts useful information from it — without any manual reading of the code.

It works in seven steps:

1. **Finds all Java projects** in the source folder and maps out their structure (modules, files, build setup).
2. **Reads each Java file** and understands its structure — which classes, interfaces, and packages it contains. This is powered by [tree-sitter](https://tree-sitter.github.io/), a fast source-code parser.
3. **Extracts import declarations** — captures all import statements with metadata including static imports, wildcard imports, and line numbers.
4. **Extracts class members** — the fields, methods, and constructors defined in each class.
5. **Detects Spring components** — identifies which classes are controllers, services, repositories, or entities based on their annotations (e.g. `@RestController`, `@Service`).
6. **Finds dependency relationships** — identifies which classes depend on which other classes through Spring's dependency injection (`@Autowired`).
7. **Maps structural relationships** — records which classes extend or implement others, which methods call which other methods, and which types use which imports.

At the end, it prints a summary of everything found across all repositories.

## How to run

Normal pipeline execution uses the canonical parser runner:

```bash
cd POC
PYTHONPATH=.:2_Parsers python3 2_Parsers/parser_pipeline.py
```

This runs Java, OpenAPI, and Markdown parsing and writes the normalized JSON contract for extraction.

Use the Java parser entry point only for isolated parser tests or debugging.

From the `POC` folder:

```bash
source .venv/bin/activate
PYTHONPATH=.:2_Parsers python3 2_Parsers/java_parser/main.py
```

By default, source code is read from `POC/DataSource/code_projects`. To point it at a different folder:

```bash
JAVA_PARSER_SOURCE_DIR=/path/to/repos PYTHONPATH=.:2_Parsers python3 2_Parsers/parser_pipeline.py
```

## Import Extraction

The parser extracts import declarations as separate entities, enabling dependency analysis and cross-reference resolution.

### Import Entity Schema

Each import statement is extracted as an `Import` entity with:

- **type**: `"Import"`
- **name**: Fully-qualified import name (e.g. `"java.util.List"`)
- **source**: Parser-generated document ID
- **repository**: Repository name
- **module**: Module name
- **package**: Package of the file containing the import
- **file_path**: Source file path
- **is_static**: `true` for static imports
- **is_wildcard**: `true` for wildcard imports (`.*`)
- **start_line**: Line number (1-indexed)
- **end_line**: Line number (1-indexed)
- **imported_name**: Simple name being imported

### Example Import Entity

```json
{
  "type": "Import",
  "name": "java.util.List",
  "source": "java_parser:repo:module:src/Foo.java",
  "repository": "repo",
  "module": "module",
  "package": "com.example",
  "file_path": "src/Foo.java",
  "is_static": false,
  "is_wildcard": false,
  "start_line": 5,
  "end_line": 5,
  "imported_name": "List"
}
```

### IMPORTS Relationships

The parser creates `IMPORTS` relationships from type declarations (Class, Interface, Enum) to the import entities declared in the same file.

Each relationship has:

- **type**: `"IMPORTS"`
- **source**: Type entity identifier (e.g. `"Class:com.example.Foo"`)
- **target**: Import entity identifier (e.g. `"Import:java.util.List"`)
- **properties**: Metadata about source and target entities

This enables queries like:
- Which classes import a specific library?
- What external dependencies does a class use?
- Which types depend on deprecated imports?

## Testing

Run the Java parser tests:

```bash
cd POC
source .venv/bin/activate
python -m pytest 2_Parsers/java_parser/tests/ -v
```

Import extraction is tested in `tests/test_import_extraction.py` with coverage for:
- Regular imports
- Static imports
- Wildcard imports
- Multiple imports per file
- Import-to-entity conversion
- IMPORTS relationship creation

