A good way to implement this is to split the concept into **incremental vertical slices** where each chunk produces a usable artifact and has a clear home:

* `POC/2_Parsers` → **raw source → parsed structural representation**
* `POC/3_Extractors` → **parsed representation → semantic entities, triples, embeddings**
* `POC/4_Graph_Normalisation` → **extracted knowledge → graph-ready normalized model**

The parser layer should **not directly create Neo4j nodes**. Keep the intermediate representation stable so you can change extraction models later.

Below is a proposed implementation backlog.

---

# Phase 0 — Project Foundation

## Chunk 0.1 — Folder structure and shared contracts

**Folder**

```
POC/
 ├── 2_Parsers/
 ├── 3_Extractors/
 ├── 4_Graph_Normalisation/
 ├── shared/
 └── tests/
```

**Goal**

Create common models shared between all pipelines.

**Implement**

* Entity model
* Relationship model
* Source metadata model
* Extraction result model
* Pipeline context model

Example:

```python
Entity
-------
id
type
name
source
properties


Relationship
-------------
source_entity
target_entity
type
properties
confidence
```

**Output**

```
POC/shared/models/
```

---

# Phase 1 — Java Parser

## Chunk 1.1 — Java project discovery

**Folder**

```
POC/2_Parsers/java_parser/
```

**Goal**

Discover Spring Boot source files.

Implement:

* Scan directories
* Detect `.java`
* Detect Maven/Gradle projects
* Build file inventory

Output:

```json
{
 "file": "UserController.java",
 "package": "com.bank.user",
 "lines": 240
}
```

---

## Chunk 1.2 — Java AST parser

**Folder**

```
POC/2_Parsers/java_parser/
```

**Technology**

Use:

* Tree-sitter Java
* JavaParser
* Eclipse JDT

Extract:

* Package
* Imports
* Classes
* Interfaces
* Enums

Output:

```json
{
"type":"class",
"name":"PaymentController",
"package":"com.bank.payment"
}
```

---

## Chunk 1.3 — Java member extraction

**Folder**

```
POC/2_Parsers/java_parser/
```

Extract:

* Methods
* Fields
* Constructors
* Parameters

Output:

```json
{
"type":"method",
"name":"createPayment",
"class":"PaymentController",
"parameters":[]
}
```

---

## Chunk 1.4 — Spring annotation extractor

**Folder**

```
POC/2_Parsers/java_parser/
```

Extract:

Controllers:

```
@RestController
@RequestMapping
@GetMapping
@PostMapping
```

Services:

```
@Service
```

Repositories:

```
@Repository
```

Components:

```
@Component
```

Entities:

```
@Entity
```

---

## Chunk 1.5 — Dependency injection extractor

**Folder**

```
POC/2_Parsers/java_parser/
```

Extract:

```java
@Autowired
private PaymentService service;
```

Relationship:

```
PaymentController
       |
       USES
       |
PaymentService
```

---

## Chunk 1.6 — Java relationship extractor

**Folder**

```
POC/2_Parsers/java_parser/
```

Extract:

* inheritance
* interface implementation
* method calls

Examples:

```
PaymentService IMPLEMENTS PaymentProcessor


PaymentController CALLS PaymentService.create()
```

---

# Phase 2 — Markdown Parser

## Chunk 2.1 — Document ingestion

**Folder**

```
POC/2_Parsers/markdown_parser/
```

Use:

* LlamaIndex SimpleDirectoryReader

Input:

```
POC/DataSource/berlin_group_pdf_chunks
```

Output:

Document objects.

---

## Chunk 2.2 — Semantic chunking

**Folder**

```
POC/2_Parsers/markdown_parser/
```

Use:

```
SemanticSplitterNodeParser
```

Output:

```json
{
chunk_id:"bg_001",
text:"Payment initiation API..."
}
```

---

## Chunk 2.3 — Markdown structure extraction

**Folder**

```
POC/2_Parsers/markdown_parser/
```

Extract:

* headings
* sections
* references
* tables

Output:

```json
{
section:"Payment Initiation",
parent:"AIS"
}
```

---

# Phase 3 — OpenAPI Parser

## Chunk 3.1 — YAML loader

**Folder**

```
POC/2_Parsers/openapi_parser/
```

Input:

```
POC/DataSource/yaml_spec
```

Extract:

* OpenAPI metadata
* version
* title

---

## Chunk 3.2 — Endpoint extraction

**Folder**

```
POC/2_Parsers/openapi_parser/
```

Extract:

```
GET /payments
POST /accounts
```

Output:

```json
{
type:"endpoint",
method:"POST",
path:"/payments"
}
```

---

## Chunk 3.3 — Schema extraction

**Folder**

```
POC/2_Parsers/openapi_parser/
```

Extract:

* DTOs
* enums
* properties

Output:

```json
{
type:"schema",
name:"PaymentRequest"
}
```

---

## Chunk 3.4 — Reference resolver

**Folder**

```
POC/2_Parsers/openapi_parser/
```

Resolve:

```
$ref:
#/components/schema/Payment
```

Create:

```
Endpoint
    RETURNS
PaymentResponse
```

---

# Phase 4 — Entity Extraction

Now move from syntax → knowledge.

---

# Chunk 4.1 — spaCy pipeline foundation

**Folder**

```
POC/3_Extractors/spacy/
```

Implement:

* custom pipeline
* domain vocabulary
* entity matcher

Entities:

```
Payment
Account
Consent
Customer
Transaction
```

---

# Chunk 4.2 — Rule based version tagging

**Folder**

```
POC/3_Extractors/spacy/
```

Detect:

```
PSD2 v1.3.16
Berlin Group V2
OpenAPI 3.0
```

Attach:

```json
{
entity:"Payment API",
version:"1.3.16"
}
```

---

# Chunk 4.3 — GLM-5 structured extraction

**Folder**

```
POC/3_Extractors/glm/
```

Input:

Parsed chunks.

Output:

JSON schema:

```json
{
entities:[
],
relationships:[
]
}
```

---

# Chunk 4.4 — Triple extraction

**Folder**

```
POC/3_Extractors/glm/
```

Generate:

```
PaymentInitiation
     USES
PaymentService
```

---

# Chunk 4.5 — Qwen embedding generation

**Folder**

```
POC/3_Extractors/embeddings/
```

Generate:

```
entity_embedding
chunk_embedding
```

Store:

```json
{
entity:"Payment",
vector:[...]
}
```

---

# Phase 5 — Graph Normalisation

---

# Chunk 5.1 — Canonical entity model

**Folder**

```
POC/4_Graph_Normalisation/entities/
```

Create rules:

Example:

Java:

```
PaymentController
```

OpenAPI:

```
POST /payments
```

Documentation:

```
Payment Initiation
```

Become:

```
PaymentInitiation
```

---

# Chunk 5.2 — Entity deduplication

**Folder**

```
POC/4_Graph_Normalisation/entities/
```

Implement:

* name similarity
* embedding similarity
* domain rules

Example:

Merge:

```
PaymentDTO
PaymentRequest
Payment Initiation Request
```

---

# Chunk 5.3 — Relationship normalization

**Folder**

```
POC/4_Graph_Normalisation/relationships/
```

Map:

Raw:

```
calls
uses
depends_on
references
```

Into:

```
USES
DEPENDS_ON
IMPLEMENTS
DOCUMENTS
EXPOSES
```

---

# Chunk 5.4 — Neo4j writer

**Folder**

```
POC/4_Graph_Normalisation/neo4j/
```

Implement:

* AsyncSession
* MERGE queries
* constraints
* indexes

Example:

```cypher
MERGE (e:Entity {id:$id})
SET e += $properties
```

---

# Phase 6 — Airflow Orchestration

## Chunk 6.1 — DAG skeleton

**Folder**

```
POC/airflow/
```

Create:

```
knowledge_graph_pipeline.py
```

---

## Chunk 6.2 — TaskGroups

Tasks:

```
ingestion
   |
parsers
   |
extractors
   |
normalisation
   |
neo4j_load
```

---

## Chunk 6.3 — Incremental execution

Implement:

* file checksum
* changed document detection
* changed source detection

---

# Recommended Implementation Order

Build in this order:

```
1. Shared models
        |
2. Java parser
        |
3. OpenAPI parser
        |
4. Markdown parser
        |
5. Normalized JSON output
        |
6. spaCy extractor
        |
7. LLM extraction
        |
8. Embeddings
        |
9. Neo4j loader
        |
10. Airflow
```

This gives you a working pipeline early:

```
Spring Code
     |
Java Parser
     |
Normalized JSON
     |
Neo4j
```

before adding LLM complexity.

A practical next step would be to create a **Git-style implementation backlog** where every chunk becomes a small task with:

* task ID
* folder
* files to create
* dependencies
* acceptance criteria
* test cases.
