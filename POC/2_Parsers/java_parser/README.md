# Java Parser

## What it does

This component reads Java source code from the configured repositories and automatically extracts useful information from it — without any manual reading of the code.

It works in seven steps:

1. **Finds all Java projects** in the source folder and maps out their structure (modules, files, build setup).
2. **Reads each Java file** and understands its structure — which classes, interfaces, enums, and packages it contains. This is powered by [tree-sitter](https://tree-sitter.github.io/), a fast source-code parser.
3. **Extracts import declarations** — captures all import statements with metadata including static imports, wildcard imports, and line numbers.
4. **Extracts class members** — the fields, methods, and constructors defined in each class.
5. **Detects Spring components** — identifies which classes are controllers, services, repositories, or entities based on their annotations (e.g. `@RestController`, `@Service`).
6. **Finds dependency relationships** — identifies which classes depend on which other classes through Spring's dependency injection (`@Autowired`).
7. **Maps structural relationships** — records which classes extend or implement others, which methods call which other methods, which types use which imports, and how packages relate to each other.

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

### Package Entity Schema

Each unique package is extracted as a `Package` entity with:

- **type**: `"Package"`
- **name**: Package qualified name
- **qualified_name**: Same as `name`
- **source**: Parser-generated package identifier
- **repository**: Repository name
- **module**: Module name
- **file_path**: Representative source directory for the package

### Example Package Entity

```json
{
  "type": "Package",
  "name": "com.example.app",
  "qualified_name": "com.example.app",
  "source": "java_parser:repo:module:com.example.app",
  "repository": "repo",
  "module": "module",
  "file_path": "src/main/java/com/example/app"
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

### Package Relationships

Package entities are deduplicated by qualified name and emitted in a deterministic first-seen order.

The parser creates these package-level relationships when the target package is present in the parsed codebase:

- `CONTAINS` from Package to Class / Interface / Enum
- `CONTAINS` from parent Package to nested Package
- `IMPORTS` from Package to Package
- `BELONGS_TO` from Package to Module

Package hierarchy is preserved by linking direct parent packages only, so `java.util` contains `java.util.concurrent` when both packages exist in the parsed module.

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
- Package entity extraction and package relationship creation

Annotation attribute extraction is tested in `tests/test_annotation_attributes.py` with coverage for:
- Marker annotations (no attributes)
- Single string value: `@Value("${prop}")`
- Named boolean attribute: `@Autowired(required = false)`
- Named enum attribute: `@RequestMapping(method = RequestMethod.POST)`
- Array attribute: `@RequestMapping(produces = {"json", "xml"})`
- Multiple named attributes
- Import-based FQN resolution
- Spring annotations (`@RequestMapping`, `@Value`, `@Autowired`)
- Lombok annotations (`@Data`, `@Builder`)
- Validation annotations (`@NotNull`, `@Size`)

## Annotation Attribute Extraction

Annotations are extracted as structured objects with fully-parsed attribute values,
not as raw text. The extraction happens at the AST level using tree-sitter nodes.

### Supported attribute value types

| Type | Example | Extracted as |
|---|---|---|
| String literal | `"text"` | `str` (quotes stripped) |
| SpEL expression | `"${prop.name}"` | `str` (quotes stripped) |
| Numeric | `123` | `str` |
| Boolean | `true` / `false` | `str` |
| Enum reference | `RequestMethod.POST` | `str` |
| Array | `{"json", "xml"}` | `list[str]` |
| Nested annotation | `@JsonProperty(...)` | raw text `str` |

Single unnamed arguments are stored under the conventional `"value"` key.

### Example annotation entities

```json
{
  "name": "@RequestMapping",
  "qualified_name": "org.springframework.web.bind.annotation.RequestMapping",
  "attributes": {
    "value": "/api/v1/accounts",
    "method": "RequestMethod.GET"
  }
}
```

```json
{
  "name": "@Value",
  "qualified_name": "org.springframework.beans.factory.annotation.Value",
  "attributes": {
    "value": "${aspsp.profile.baseUrl}"
  }
}
```

```json
{
  "name": "@RequestMapping",
  "qualified_name": "org.springframework.web.bind.annotation.RequestMapping",
  "attributes": {
    "produces": ["application/json", "application/xml"]
  }
}
```

### Embedded annotations in entity dicts

All entity types (Class, Interface, Enum, Method, Constructor, Field, Parameter)
include a normalized `annotations` list directly in the entity dict:

```json
{
  "type": "Class",
  "name": "AccountController",
  "annotations": [
    {
      "name": "@RestController",
      "qualified_name": "org.springframework.web.bind.annotation.RestController",
      "attributes": {}
    },
    {
      "name": "@RequestMapping",
      "qualified_name": "org.springframework.web.bind.annotation.RequestMapping",
      "attributes": { "value": "/api/v1" }
    }
  ]
}
```

## Field Type Relationships

The parser creates `HAS_TYPE` relationships linking Field entities to their declared types.

### HAS_TYPE Relationship

Each Field entity gets a `HAS_TYPE` relationship to its declared type entity:

- **type**: `"HAS_TYPE"`
- **source**: Field entity UUID
- **target**: Type entity UUID (or type name if unresolved)
- **properties**:
  - `field_name`: Name of the field
  - `type_name`: Full type declaration (e.g., `"List<Account>"`, `"String[]"`)
  - `base_type`: Core type without generics/arrays (e.g., `"List"`, `"String"`)
  - `is_collection`: `true` if base type is List/Set/Map/Queue/Deque/Stack
  - `is_generic`: `true` if type has generic parameters
  - `generic_arguments`: List of type argument names (if generic)
  - `target_resolved`: `false` if type entity was not found in codebase

### Type Support

The parser handles:

- **Simple types**: `String`, `int`, `double`
- **Custom classes**: `Account`, `Payment`
- **Generic types**: `List<Account>`, `Map<String, Integer>`
- **Array types**: `String[]`, `int[]`
- **Collection types**: `List<T>`, `Set<T>`, `Map<K,V>`, `Queue<T>`, `Deque<T>`, `Stack<T>`
- **Nested generics**: `Map<String, List<Account>>`

### Example HAS_TYPE Relationships

Simple field type:

```json
{
  "type": "HAS_TYPE",
  "source": "uuid-field-name",
  "target": "uuid-class-String",
  "properties": {
    "field_name": "name",
    "type_name": "String",
    "base_type": "String",
    "is_collection": false,
    "is_generic": false
  }
}
```

Collection field type:

```json
{
  "type": "HAS_TYPE",
  "source": "uuid-field-accounts",
  "target": "uuid-interface-List",
  "properties": {
    "field_name": "accounts",
    "type_name": "List<Account>",
    "base_type": "List",
    "is_collection": true,
    "is_generic": true,
    "generic_arguments": ["Account"]
  }
}
```

Unresolved type:

```json
{
  "type": "HAS_TYPE",
  "source": "uuid-field-external",
  "target": "ThirdPartyClass",
  "properties": {
    "field_name": "external",
    "type_name": "ThirdPartyClass",
    "base_type": "ThirdPartyClass",
    "is_collection": false,
    "is_generic": false,
    "target_resolved": false
  }
}
```

### Use Cases

HAS_TYPE relationships enable:

- Type dependency graph construction
- Data flow analysis through field types
- Type usage tracking across the codebase
- Refactoring impact analysis
- Dead code detection (unused types)
- Complexity metrics (depth of type hierarchies)

## Parameter Type Relationships

The parser creates `HAS_TYPE` relationships linking Parameter entities to their declared types.

### Parameter HAS_TYPE Relationship

Each Parameter entity gets a `HAS_TYPE` relationship to its declared type entity:

- **type**: `"HAS_TYPE"`
- **source**: Parameter entity UUID
- **target**: Type entity UUID (or type name if unresolved)
- **properties**:
  - `parameter_name`: Name of the parameter
  - `type_name`: Full type declaration (varargs normalized to `Type...`)
  - `base_type`: Core type without generics/arrays (e.g., `"List"`, `"String"`)
  - `is_collection`: `true` for collection-like declarations and varargs
  - `is_generic`: `true` if type has generic parameters
  - `is_varargs`: `true` for varargs parameters
  - `generic_arguments`: List of type argument names (if generic)
  - `target_resolved`: `false` if type entity was not found in codebase

### Parameter Type Support

The parser handles:

- **Simple types**: `String`, `int`, `double`
- **Custom classes**: `Account`, `Payment`
- **Generic types**: `List<Account>`, `Map<String, Integer>`
- **Array types**: `String[]`, `int[]`
- **Varargs types**: `String... values`
- **Nested generics**: `Map<String, List<Account>>`

### Example Parameter HAS_TYPE Relationships

Simple parameter type:

```json
{
  "type": "HAS_TYPE",
  "source": "uuid-parameter-name",
  "target": "uuid-class-String",
  "properties": {
    "parameter_name": "name",
    "type_name": "String",
    "base_type": "String",
    "is_collection": false,
    "is_generic": false,
    "is_varargs": false
  }
}
```

Varargs parameter type:

```json
{
  "type": "HAS_TYPE",
  "source": "uuid-parameter-values",
  "target": "uuid-class-String",
  "properties": {
    "parameter_name": "values",
    "type_name": "String...",
    "base_type": "String",
    "is_collection": true,
    "is_generic": false,
    "is_varargs": true
  }
}
```

## Enhanced CALLS Relationships

The parser emits enriched `CALLS` relationships for method invocations and constructor calls.

### CALLS Relationship Properties

Each `CALLS` relationship includes top-level provenance fields and a `properties` object with:

- `source_method`: Enclosing caller method/constructor name
- `target_method`: Called method name (`<init>` for constructors)
- `target_class`: Receiver expression or constructor type
- `call_site_line`: 1-based source line where call appears
- `is_static`: `true` for static-style calls (e.g., `Math.max(...)`)
- `receiver_type`: Receiver expression/type as extracted from AST
- `receiver_variable`: Receiver variable for instance calls when available
- `argument_count`: Number of call arguments
- `argument_types`: Inferred argument type labels in call order
- `method_signature`: Derived signature string, e.g. `format(String, int)`
- `is_constructor`: `true` for `new Type(...)` calls

When method entities are resolvable in the same module output, the relationship also includes:

- `source_entity_id`: Source method/constructor UUID
- `target_entity_id`: Target method/constructor UUID (best effort)

### Static vs Instance Detection

Static detection uses AST-level heuristics on receiver text:

- `Math.max(a, b)` → static call (`is_static: true`)
- `account.getBalance()` → instance call (`is_static: false`)

This is syntactic extraction. Full semantic type resolution is deferred to downstream graph stages.

### Chain Call Handling

Call chains create one `CALLS` relationship per invocation in the chain.

Example: `account.getOwner().getName()` emits two call edges:

- `getOwner()`
- `getName()`

Both include the same call-site line with per-invocation method metadata.

## Spring Bean Injection Relationships

The parser emits `INJECTS_BEAN` relationships to represent Spring-managed dependency injection points.

### Supported injection annotations

- `@Autowired`
- `@Inject` (JSR-330)
- `@Resource` (JSR-250)

### Supported injection styles

- Field injection
- Constructor injection
- Setter injection

### Qualifier and bean selection metadata

The parser extracts qualifier and bean-selection hints from:

- `@Qualifier("beanName")`
- `@Named("beanName")`
- `@Resource(name = "beanName")`
- `@Primary` (captured as `is_primary` on target when available)

`@Autowired(required = false)` is captured as `required: false`.

### INJECTS_BEAN relationship shape

Each relationship includes:

- `source_entity_id` and `target_entity_id` (best effort UUID linking)
- `properties.injection_type` (`field`, `constructor`, `setter`)
- `properties.framework` (`spring`)
- `properties.annotation`
- `properties.required`
- `properties.qualifier`
- `properties.bean_name`
- `properties.field_name` or constructor/setter parameter metadata


