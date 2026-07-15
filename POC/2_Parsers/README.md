# Parser Pipeline

- Purpose: run Java, OpenAPI, and Markdown parsers as one Stage 2 pipeline.
- Normal entry point: `python3 2_Parsers/parser_pipeline.py` from `POC/`.
- Execution order: Java Parser, then OpenAPI Parser, then Markdown Parser.
- Combined output: `settings.parser_output_dir/java_openapi_markdown_parser_output.json`.
- Direct Java output: one module file per Java module under `settings.parser_output_dir/java_code/`.
- Direct OpenAPI output: one spec file under `settings.parser_output_dir/openapi_specs/` per YAML/YML file.
- Direct Markdown output: `markdown_parser_output.json`.
- Contract: normalized JSON with `entities`, `relationships`, `documents`, `source_metadata`, `provenance`, and `version_metadata`.
- Downstream stages consume only this normalized JSON contract.
- Individual parser modules remain independently testable, but normal execution should use this runner.

## Entity Types

The Java parser extracts the following entity types:
- **Class**, **Interface**, **Enum**: Type declarations
- **Method**, **Field**, **Constructor**: Class members
- **Parameter**: Method and constructor parameters (extracted as separate entities)
- **Annotation**: Annotations applied to types, members, and parameters (extracted as separate entities)
- **Import**: Import declarations (with static/wildcard metadata)

### Annotation Entity Schema

Annotations are extracted as first-class entities to enable annotation-level querying, relationship tracking, and pattern analysis.

**Fields:**
- `type`: Always "Annotation"
- `name`: Annotation name with @ prefix (e.g., "@Data")
- `simple_name`: Simple name without @ prefix (e.g., "Data")
- `qualified_name`: Fully qualified annotation name (e.g., "lombok.Data")
- `attributes`: Dictionary of annotation attributes (if any)
- `target_type`: Type of annotated element ("Class", "Method", "Field", "Parameter", "Constructor")
- `target_name`: Name of the annotated element
- `file_path`: Repository-relative source file path
- `repository`: Repository name
- `module`: Module label
- `start_line`: Line number where annotation appears
- `end_line`: Line number (typically same as start_line)
- `source`: Document ID
- `uuid`: Unique identifier

**Example:**
```json
{
  "type": "Annotation",
  "name": "@Column",
  "simple_name": "Column",
  "qualified_name": "javax.persistence.Column",
  "attributes": {
    "name": "user_id",
    "nullable": "false"
  },
  "target_type": "Field",
  "target_name": "userId",
  "file_path": "com/example/User.java",
  "repository": "user-service",
  "module": "user-service",
  "start_line": 15,
  "end_line": 15,
  "source": "java_parser:user-service:user-service:com/example/User.java",
  "uuid": "ann-uuid-123"
}
```

**Note:** Type, method, field, parameter, and constructor entities now include an `annotation_count` property instead of inline `annotations` arrays.

### Parameter Entity Schema

Parameters are extracted as first-class entities to enable parameter-level querying and relationship tracking.

**Fields:**
- `type`: Always "Parameter"
- `name`: Parameter identifier
- `parameter_type`: Type of the parameter (e.g., "String", "List<String>", "int[]")
- `position`: Zero-based position in the parameter list
- `is_vararg`: Boolean indicating varargs parameter (e.g., `String... args`)
- `annotation_count`: Number of annotations applied to the parameter
- `uuid`: Unique identifier
- `method_name`: Name of the owning method or constructor
- `method_qualified_name`: Fully qualified name of the owning method/constructor
- `file_path`: Repository-relative source file path
- `repository`: Repository name
- `module`: Module label
- `start_line`: Line number where the parameter is defined
- `source`: Document ID

**Example:**
```json
{
  "type": "Parameter",
  "name": "userId",
  "parameter_type": "String",
  "position": 0,
  "is_vararg": false,
  "annotation_count": 2,
  "uuid": "param-uuid-456",
  "method_name": "getUser",
  "method_qualified_name": "com.example.UserController.getUser",
  "file_path": "com/example/UserController.java",
  "repository": "user-service",
  "module": "user-service",
  "start_line": 42,
  "source": "java_parser:user-service:user-service:com/example/UserController.java"
}
```
and `annotation_count` property instead of inline arrays.

## Relationship Types

The parser creates the following relationships:
- **EXTENDS**: Inheritance relationships
- **IMPLEMENTS**: Interface implementation
- **CALLS**: Method invocations and constructor calls (see details below)
- **INJECTS**: Dependency injection
- **IMPORTS**: Type-to-import relationships
- **HAS_PARAMETER**: Method/Constructor to Parameter relationships (preserves parameter order)
- **HAS_ANNOTATION**: Element to Annotation relationships (links annotated elements to their annotations)
- **ANNOTATION_TYPE**: Annotation to its declaration (when annotation class exists in codebase)

### HAS_ANNOTATION Relationship Schema

Links classes, methods, fields, parameters, and constructors to their annotation entities.

**Fields:**
- `type`: Always "HAS_ANNOTATION"
- `source`: UUID of the annotated element entity
- `target`: UUID of the Annotation entity
- `properties.target_type`: Type of annotated element for context

**Example:**
```json
{
  "type": "HAS_ANNOTATION",
  "source": "field-uuid-789",
  "target": "ann-uuid-123",
  "properties": {
    "target_type": "Field"
  }
}
```

**Usage Pattern:**

To query all annotations on a class:
```cypher
MATCH (c:Class {name: "User"})-[:HAS_ANNOTATION]->(a:Annotation)
RETURN a
```

### ANNOTATION_TYPE Relationship Schema

Links annotation entities to their declaration when the annotation class exists in the codebase.

**Fields:**
- `type`: Always "ANNOTATION_TYPE"
- `source`: UUID of the Annotation entity
- `target`: UUID of the annotation's Class/Interface declaration
- `properties`: Empty dictionary

**Example:**
```json
{
  "type": "ANNOTATION_TYPE",
  "source": "ann-uuid-123",
  "target": "class-uuid-custom-annotation",
  "properties": {}
}
```

**Usage Pattern:**

To find all usages of a custom annotation:
```cypher
MATCH (annotationDecl:Class {name: "MyCustomAnnotation"})
      <-[:ANNOTATION_TYPE]-(ann:Annotation)
      <-[:HAS_ANNOTATION]-(element)
RETURN element
```
- **HAS_PARAMETER**: Method/Constructor to Parameter relationships (preserves parameter order)

### HAS_PARAMETER Relationship Schema

Links methods and constructors to their parameter entities, preserving parameter order via position metadata.

**Fields:**
- `type`: Always "HAS_PARAMETER"
- `source`: UUID of the Method or Constructor entity
- `target`: UUID of the Parameter entity
- `properties.position`: Zero-based parameter position

**Example:**
```json
{
  "type": "HAS_PARAMETER",
  "source": "method-uuid-123",
  "target": "param-uuid-456",
  "properties": {
    "position": 0
  }
}
```

**Usage Pattern:**

To query all parameters of a method:
```cypher
MATCH (m:Method {name: "processPayment"})-[r:HAS_PARAMETER]->(p:Parameter)
RETURN p ORDER BY r.position
```

### CALLS Relationship Schema

The `CALLS` relationship captures method invocations and constructor calls with comprehensive metadata:

**Core Fields:**
- `source`: Source class name
- `target`: Target identifier (receiver.method for calls, type name for constructors)
- `type`: Always "CALLS"
- `source_method`: Enclosing method name where the call occurs
- `target_method`: Called method name (or "<init>" for constructors)
- `target_class`: Receiver expression (variable/type name)

**Call Metadata:**
- `call_site_line`: Line number where the call occurs (1-based)
- `arguments_count`: Number of arguments passed
- `is_static`: Boolean indicating static method call (heuristic-based)
- `is_constructor`: Boolean indicating constructor call (new expression)
- `qualified_name`: Reserved for future use (currently null)
- `receiver_type`: Reserved for future use (currently null)

**Examples:**

Instance method call:
```json
{
  "source": "PaymentService",
  "target": "repository.save",
  "type": "CALLS",
  "source_method": "processPayment",
  "target_method": "save",
  "target_class": "repository",
  "call_site_line": 42,
  "arguments_count": 1,
  "is_static": false,
  "is_constructor": false
}
```

Static method call:
```json
{
  "source": "PaymentService",
  "target": "ValidationUtils.validateAmount",
  "type": "CALLS",
  "source_method": "processPayment",
  "target_method": "validateAmount",
  "target_class": "ValidationUtils",
  "call_site_line": 38,
  "arguments_count": 2,
  "is_static": true,
  "is_constructor": false
}
```

Constructor call:
```json
{
  "source": "PaymentService",
  "target": "Payment",
  "type": "CALLS",
  "source_method": "createPayment",
  "target_method": "<init>",
  "target_class": "Payment",
  "call_site_line": 55,
  "arguments_count": 3,
  "is_static": false,
  "is_constructor": true
}
```

**Call Type Detection:**

The parser uses syntactic heuristics to identify call types:
- **Static calls**: Receiver contains an uppercase-starting identifier (e.g., `Utils.method()`, `com.example.Helper.doWork()`)
- **Instance calls**: Receiver starts with lowercase (e.g., `object.method()`)
- **Constructor calls**: Uses `new` keyword (e.g., `new ArrayList<>()`)
- **Super/this calls**: Explicit `super` or `this` receivers

**Chained Calls:**

Each method in a chain creates a separate relationship:
```java
builder.setA().setB().build();
// Creates 3 CALLS relationships:
// 1. builder.setA
// 2. (intermediate).setB
// 3. (intermediate).build
```

**Limitations:**

**Limitations:**

- External method signatures are not resolved
- Type resolution is deferred to graph normalization
- Static call detection is heuristic-based (syntactic analysis only)
- Generic type parameters are stripped from constructor types

## OpenAPI Parser

The OpenAPI parser extracts structured metadata from OpenAPI 3.x specifications.

### Schema Entity with $ref Tracking

Schema entities now include comprehensive $ref resolution tracking to enable impact analysis and change tracking:

**$ref Tracking Fields:**
- `is_reference`: Boolean - true if this entity is itself a $ref to another definition
- `ref_path`: String - original $ref path if is_reference is true (e.g., "#/components/schemas/Account")
- `refs`: Array - all $ref paths contained within this schema (allOf/oneOf/anyOf/properties)
- `external_refs`: Array - $ref paths pointing to external files or URLs
- `circular_refs`: Array - $ref paths that form circular references
- `ref_dereferenced`: Boolean - true if all refs have been successfully resolved

**Example Schema Entity:**
```json
{
  "type": "Schema",
  "name": "PaymentRequest",
  "schema_type": "object",
  "description": "Payment request DTO",
  "properties": [
    {"name": "amount", "type": "number", "required": true},
    {"name": "currency", "ref": "#/components/schemas/Currency", "required": true}
  ],
  "required": ["amount", "currency"],
  "refs": ["#/components/schemas/Base", "#/components/schemas/Currency"],
  "is_reference": false,
  "ref_path": null,
  "external_refs": [],
  "circular_refs": [],
  "ref_dereferenced": true
}
```

**Reference Resolution:**

The parser tracks $ref resolution through multiple stages:
1. **Detection**: Identifies all $ref strings during schema extraction
2. **Classification**: Separates internal (#/...) from external (file/URL) refs
3. **Resolution**: Attempts to dereference internal refs to their targets
4. **Cycle Detection**: Identifies circular reference patterns
5. **Metadata Preservation**: Records resolution status and original paths

**External References:**

External $ref paths are preserved but not resolved:
```json
{
  "name": "Account",
  "refs": ["./common.yaml#/components/schemas/Address"],
  "external_refs": ["./common.yaml#/components/schemas/Address"],
  "ref_dereferenced": false
}
```

**Circular References:**

Circular references are detected and flagged:
```json
{
  "name": "Node",
  "refs": ["#/components/schemas/Node"],
  "circular_refs": ["#/components/schemas/Node"],
  "ref_dereferenced": false
}
```

**Use Cases:**
- Impact analysis: Find all schemas that reference a given schema
- Change tracking: Identify which entities are affected by schema changes
- External dependency tracking: List all external spec files referenced
- Circular dependency detection: Identify problematic reference cycles

Configuration is centralized in `shared.config`.
Use `POC/config.yml` for non-sensitive values and `POC/.env` for secrets only.
