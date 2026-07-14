# Knowledge Graph AI Platform — Architecture Review

**Source Files Reviewed**

| File | Title (from `@startuml` / `title`) |
|------|------------------------------------|
| `docs/system_design/architectures/puml/codingAssistance_architecture.puml` | KG_AI_Platform_Overview |
| `docs/system_design/architectures/puml/codingAssistance_architecture_L0.puml` | KG_AI_Platform_Layer0 — External Spec Acquisition |
| `docs/system_design/architectures/puml/codingAssistance_architecture_L1.puml` | KG_AI_Platform_Layer1 — Data Sources |
| `docs/system_design/architectures/puml/codingAssistance_architecture_L2.puml` | KG_AI_Platform_Layer2 — Ingestion & Processing |
| `docs/system_design/architectures/puml/codingAssistance_architecture_L3.puml` | KG_AI_Platform_Layer3 — Knowledge Graph Platform |
| `docs/system_design/architectures/puml/codingAssistance_architecture_L4.puml` | KG_AI_Platform_Layer4 — AI Services / APIs |
| `docs/system_design/architectures/puml/codingAssistance_architecture_L5.puml` | KG_AI_Platform_Layer5 — AI Consumers |
| `docs/system_design/architectures/puml/codingAssistance_architecture_L6.puml` | KG_AI_Platform_Layer6 — End Users & Outputs |

All eight files were read in full. Every finding below is traceable to a specific element, alias, arrow, label, or note in those files.

---

## 1. Tech Stack Recommendation

> One table per layer. Tools named in the .puml are evaluated on merit. **Comment** column is reserved for senior architect review.

---

### Layer 0 — "External Spec Acquisition (Multi-Version)"

| Component (.puml alias) | Recommended Tool | Justification | Alternatives | Tradeoffs | Comment |
|---|---|---|---|---|---|
| `MarkitDown` — PDF → Markdown | **Docling v2** (`docling`, IBM) | - `PDFSpec_v1` / `PDFSpec_v2` are table-heavy regulatory specs<br>- Docling reconstructs tables as proper Markdown, preserving structure needed by `ParsingChunking` | - Microsoft MarkItDown | - **Docling**: ~2 GB model; better table fidelity<br>- **MarkItDown**: ~30 MB; fast but flattens tables to prose | |
| Download trigger (`BerlinGroup_v1` / `v2`) | **Apache Airflow 2.x** | - .puml defines no orchestration for download timing<br>- Airflow DAG can chain directly into L2 ingestion DAG on success | - GitLab CI scheduled pipeline | - **Airflow**: cross-DAG dependencies, retry logic; requires separate cluster<br>- **GitLab CI**: zero extra infra; cannot natively trigger external pipelines | |
| YAML pull (`GitLab_ngpsd2` / `GitLab_of`) | **`python-gitlab`** (via Airflow `PythonOperator`) | - Both repos are GitLab-hosted<br>- No `git` binary required; works inside Docker; handles token rotation | - `git clone` / `git pull` in CI | - **python-gitlab**: cleaner containerisation; no SSH keys<br>- **git clone**: keeps full commit history; enables SHA-based incremental pull | |
| `L0_v3` (proposed, empty) | **Cannot recommend** | - Package body is empty; .puml note: "No acquisition source defined — pending Berlin Group publication" | — | — | |

---

### Layer 1 — "Data Sources (version-tagged)"

> .puml specifies no storage medium for Markdown or YAML artifacts. See Q-5.

| Component (.puml alias) | Recommended Tool | Justification | Alternatives | Tradeoffs | Comment |
|---|---|---|---|---|---|
| `GitLabMonorepo` | **GitLab self-hosted** (CE or EE) | - Named in .puml; `AccountController` / `AccountControllerV2` naming convention cited as version markers<br>- Self-hosted controls access tokens used by L4 `AccessControlGateway` | - GitHub Enterprise Server | - **GitLab**: unified CI + source; native webhook to L5 `PipelineService`<br>- **GitHub**: larger Copilot Extensions ecosystem if `IDEExtensions` needs Copilot Enterprise | |
| `MarkdownSpecs` storage | **MinIO** (S3-compatible, versioning on) | - .puml is silent on medium<br>- Object versioning supports L3 "Schema Traceability" and "Cross-Version Diffs" without polluting git log | - Dedicated GitLab repo (`specs-markdown`) | - **MinIO**: S3-compatible; future cloud migration is a config change<br>- **GitLab repo**: MR-based spec review workflow; no extra infra | |
| `SpecYAMLFiles` storage | **MinIO** (same instance, separate key prefix) | - Same rationale as `MarkdownSpecs`<br>- Single access-controlled store simplifies `RepoDocSync` read path in L2 | - Dedicated GitLab repo (`specs-yaml`) | Same as above | |

---

### Layer 2 — "Ingestion & Processing"

> No tools named in this layer's .puml.

| Component (.puml alias) | Recommended Tool | Justification | Alternatives | Tradeoffs | Comment |
|---|---|---|---|---|---|
| `RepoDocSync` | **LlamaIndex `SimpleDirectoryReader` + `GitLabReader`** | - Ingests `.md`, `.yaml`, and source files with file-path metadata attached<br>- Metadata feeds version-tag injection in next step | - LangChain `GitLoader` + `UnstructuredMarkdownLoader` | - **LlamaIndex**: native `Document`/`Node` model; no adapter to chunking step<br>- **LangChain**: better if team standardises on LangChain for L4 | |
| `ParsingChunking` | **LlamaIndex `SemanticSplitterNodeParser`** | - Dedicated step before `MetadataEntityExtraction` in .puml<br>- Splits on meaning boundaries; prevents YAML endpoint definitions being split mid-block | - LangChain `RecursiveCharacterTextSplitter` | - **Semantic**: preserves spec structure; requires embedding model at chunk time<br>- **Recursive**: fast, deterministic, no model dependency; loses structural awareness | |
| `MetadataEntityExtraction` | **spaCy 3.x** custom NER + rule-based version-tag injection | - `(/ version tag)` in .puml label marks this as the tagging point<br>- Version tags injected from file-path metadata (deterministic, not LLM-inferred) | - GPT-4o function calling (end-to-end extraction) | - **spaCy**: deterministic, cheap at scale<br>- **GPT-4o**: handles novel/ambiguous regulatory entities; expensive and non-deterministic | |
| `EmbeddingGeneration` | **OpenAI `text-embedding-3-large`** | - Feeds `GraphConstruction` → `Neo4jKG` "Vector Embeddings"<br>- Highest MTEB scores on financial/regulatory benchmarks | - `nomic-embed-text` v1.5 via Ollama | - **OpenAI**: best quality; data leaves premises<br>- **nomic-embed-text**: self-hosted, no egress; lower quality; needs GPU/CPU inference | |
| `RelationshipExtraction` | **GPT-4o structured output** (JSON schema, triple extraction prompt) | - Parallel branch to embedding per .puml `together {}` block<br>- Regulatory cross-references need semantic understanding; structured output feeds `GraphConstruction` directly | - Rebel (Babelscape, open-source) | - **GPT-4o**: accurate on open-domain relations; per-call cost<br>- **Rebel**: free, self-hosted, deterministic; brittle on regulatory domain | |
| `GraphConstruction` | **`neo4j` Python driver 5.x** + `MERGE` Cypher + `AsyncSession` | - Writes version-tagged nodes, embeddings, and relationships to `Neo4jKG`<br>- `MERGE` ensures idempotent re-ingestion; async enables concurrent writes from both parallel branches | - LlamaIndex `Neo4jPropertyGraphStore` | - **Driver**: full Cypher control; auditable schema<br>- **LlamaIndex store**: less boilerplate; less schema flexibility | |
| `IngestionPipeline` | **Apache Airflow 2.x** (`TaskGroup` + `ExternalTaskSensor`) | - .puml note: "Graph Construction waits for both branches" → maps to Airflow `TaskGroup` join<br>- Also provides retry/DLQ absent from .puml (see Issue 10) | - Prefect 2.x | - **Airflow**: mature; native `TaskGroup` join; heavier scheduler overhead<br>- **Prefect**: simpler Python DSL; faster dev iteration; no scheduler process | |

---

### Layer 3 — "Knowledge Graph Platform"

> .puml declares a single `Neo4jKG` rectangle with no clustering annotation — single point of failure (Issue 9). See Q-7.

| Component (.puml alias) | Recommended Tool | Justification | Alternatives | Tradeoffs | Comment |
|---|---|---|---|---|---|
| `Neo4jKG` | **Neo4j Enterprise 5.x** — Causal Cluster (3 core + read replicas) | - Named in .puml; 5.x required for native vector index (`SemanticSearchAPI`)<br>- Enterprise needed for role-based ACLs ("Stakeholder ACLs" in node label)<br>- Causal cluster addresses SPOF (Issue 9) | - Amazon Neptune Analytics | - **Neo4j**: Cypher native; mature vector index; property-level RBAC<br>- **Neptune**: fully managed, auto-scales; openCypher gaps require query rewrites; no property-level ACL | |

---

### Layer 4 — "AI Services / APIs"

> No tools named in this layer's .puml.

| Component (.puml alias) | Recommended Tool | Justification | Alternatives | Tradeoffs | Comment |
|---|---|---|---|---|---|
| `AccessControlGateway` | **Kong Gateway Enterprise** (OIDC plugin + OpenTelemetry plugin) | - .puml: "Auth: GitLab / Confluence credentials; all traffic enforced here"<br>- OIDC plugin integrates with GitLab as IdP<br>- OTel plugin routes audit events (resolves `NoteAudit` — Issue 22) | - Traefik Enterprise + Keycloak | - **Kong**: GitLab OIDC out-of-box; single binary<br>- **Traefik**: better if already used as ingress controller; Keycloak adds ops overhead | |
| `SemanticSearchAPI` | **FastAPI** wrapping `db.index.vector.queryNodes()` | - L3→L4 arrow: "vector index queries (similarity search)"<br>- Thin layer adds version-filter param (v1/v2/v3) without exposing raw Cypher | - Qdrant REST API | - **FastAPI + Neo4j**: unified store; no sync overhead<br>- **Qdrant**: higher ANN QPS at scale; requires a second store to keep in sync | |
| `GraphQueryService` | **FastAPI** with parameterised Cypher query registry | - L3→L4 arrow: "Cypher / graph traversal"<br>- Named templates prevent Cypher injection (Q-8); consumers pass typed params only | - Neo4j GraphQL Library (`@neo4j/graphql`) | - **FastAPI registry**: injection-safe; schema-agnostic<br>- **GraphQL**: better for JS frontends; schema changes require migration workflow | |
| `RAGService` | **LlamaIndex `KnowledgeGraphRAGQueryEngine`** + `Neo4jPropertyGraphStore` | - L3→L4 arrow: "retrieval context (nodes + relationships)"<br>- Graph-aware retrieval returns subgraph context, not just flat chunks<br>- **LLM for generation is absent from .puml — add GPT-4o pending Q-11** | - LangChain `GraphCypherQAChain` | - **LlamaIndex**: native Neo4j graph traversal; richer retrieval context<br>- **LangChain**: simpler setup; more examples; better for shallow (1–2 hop) graphs | |
| `PromptOrchestrator` | **LangGraph** (3 named graph nodes — one per `NotePromptOrch` case) | - `NotePromptOrch` defines 3 structurally distinct flows (Case 1/2/3)<br>- LangGraph conditional routing maps each case to a node; state is inspectable and replayable<br>- **LLM dependency unstated in .puml — see Issue 11** | - LlamaIndex `AgentRunner` | - **LangGraph**: stateful multi-step flows; explicit case routing<br>- **LlamaIndex**: preferred if entire pipeline is already LlamaIndex-based | |

---

### Layer 5 — "AI Consumers"

| Component (.puml alias) | Recommended Tool | Justification | Alternatives | Tradeoffs | Comment |
|---|---|---|---|---|---|
| `IDEExtensions` | **GitHub Copilot Extensions** (private GitHub App) | - .puml label: "(hosts GitHub Copilot) (Private GitHub repo)"<br>- Only mechanism to inject custom RAG context into Copilot Chat without replacing the LLM | - JetBrains AI Assistant (custom LLM endpoint) | - **Copilot Extensions**: familiar UX for devs; locked to GitHub/VS Code ecosystem<br>- **JetBrains**: full LLM control; needed if team uses IntelliJ-family IDEs | |
| `InternalChatbot` | **Slack Bolt SDK for Python** + Socket Mode | - Serves 5 persona types per `NoteMapping`<br>- Socket Mode: no inbound firewall rule; works behind corporate network | - Microsoft Teams Bot Framework | - **Slack**: no Azure dependency; enterprise SSO integration<br>- **Teams**: right choice if adorsys is Microsoft 365; avoids dual chat platforms | |
| `ArchitectureAssistant` | **LangGraph agent** (ADR-specialised, seeded from `GraphQueryService` + `RAGService`) | - Serves Architects and Product Managers only — distinct scope from `InternalChatbot`<br>- Cross-version diff retrieval from Neo4j maps to ADR generation use case<br>- See Q-10 | - Flowise (no-code LangChain builder, self-hosted) | - **LangGraph**: multi-service tool calls in one turn; code-controlled<br>- **Flowise**: architects can modify retrieval chain via UI without engineering | |
| `DeveloperPortal` | **Backstage (CNCF)** + `@backstage/plugin-search` → `SemanticSearchAPI` | - Serves Developers and Architects<br>- `plugin-search` embeds semantic search alongside API catalog and TechDocs | - Port.io (hosted SaaS) | - **Backstage**: fully extensible; GitLab integration via community plugins; requires K8s ops<br>- **Port.io**: zero infra; faster setup; less extensible | |
| `ConfluenceReport` | **`atlassian-python-api`** (`confluence.update_page()`) via Airflow DAG | - .puml `..>` (async/scheduled) arrow maps to a scheduled Airflow task<br>- Airflow already in stack (L2); same DAG reused | - Confluence Cloud Automation | - **atlassian-python-api**: full Python control over content rendering<br>- **Confluence Automation**: no-code; only suitable for static template reports | |
| `PipelineService` | **GitLab CI/CD** custom Python job | - .puml label: "(integrated: GitLab CI/CD)"<br>- Triggered via GitLab webhook from `GitLabIssuesBoard` issue events | - Tekton Pipelines | - **GitLab CI**: native; no extra infra; webhook from Issues is built-in<br>- **Tekton**: K8s-native portability; no GitLab coupling | |
| `GitLabIssuesBoard` | **GitLab Issues API** via `python-gitlab` | - Named in .puml; `python-gitlab` already in stack (L0)<br>- `PromptOrchestrator → Out_GitLabIssues`: `POST /projects/:id/issues` | - Jira Software | - **GitLab Issues**: single platform with monorepo and CI<br>- **Jira**: right choice if adorsys uses Jira org-wide; avoids dual issue trackers | |
| `FutureAIAgents` | **Cannot recommend** | - Placeholder with no outbound arrows and deferred persona mapping<br>- Gateway already authorising traffic to undefined scope — Issue 14 | — | — | |

---

### Layer 6 — "End Users & Outputs"

> Human persona actors require no tooling. One destination system exists.

| Component (.puml alias) | Recommended Tool | Justification | Alternatives | Tradeoffs | Comment |
|---|---|---|---|---|---|
| `adorsysConfluence` | **Atlassian Confluence Cloud** (or Data Center if self-hosted required) | - Named in .puml; destination for both sync writes (`PromptOrchestrator`) and scheduled async pushes (`ConfluenceReport`)<br>- REST API v2 supports token-based auth aligned with L4 `AccessControlGateway` | - Notion | - **Confluence**: already named; existing content; space permissions and macros for regulatory reports<br>- **Notion**: simpler API; better block model for AI-generated content; only viable if Confluence not yet adopted | |

---



### Issue 1 — Arrow style inconsistency for "hosts YAML repo" relationships (L0)

**Lines involved:**
```
BerlinGroup_v1 --> PDFSpec_v1    : "download"
BerlinGroup_v1 ..> GitLab_ngpsd2 : "hosts YAML repo"
BerlinGroup_v2 --> PDFSpec_v2    : "download"
BerlinGroup_v2 ..> GitLab_of     : "hosts YAML repo"
```

The L0 legend defines `..>` as "Asynchronous or planned / future flow." The "hosts YAML repo" relationship is a permanent structural fact (Berlin Group owns the GitLab repository), not an async or planned flow. Using `..>` for a structural hosting relationship is semantically inconsistent with both the legend definition and the adjacent `-->` PDF download arrows which are also active, initiated flows. If `..>` was chosen to mean "we reference this external system without controlling it," that semantic is not defined in the legend.

---

### Issue 2 — Typo in L0 arrow label (L0)

**Line involved:**
```
GitLab_of --> YAML_v2 : "pull-p"
```

The corresponding v1 arrow reads `GitLab_ngpsd2 --> YAML_v1 : "pull"`. The label `"pull-p"` on the v2 path appears to be an editing artifact. Depending on whether this was intentional (e.g., "pull (planned)") or a typo, the distinction carries meaning: if planned, the entire v2 YAML acquisition path is unbuilt, which contradicts the v2 package being labeled "current."

---

### Issue 3 — v3 mentioned in L3 node but has no data path (L0, L1, L3)

**Elements involved:**
- `L0_v3` package: body is empty; note reads "No acquisition source defined — pending Berlin Group publication"
- `L1 MarkdownSpecs` label: `"(v1 + v2)"` — v3 omitted
- `L1 SpecYAMLFiles` label: `"(v1 + v2)"` — v3 omitted
- `Neo4jKG` label in L3: `"Every node/edge tagged with: Version  (v1 | v2 | v3)"`

The graph claims to tag nodes with v3 but no acquisition, storage, or ingestion path for v3 data is defined in any layer. The v3 tag in the Neo4j node label is aspirational at best; at worst, it implies a capability that the architecture does not yet support.

---

### Issue 4 — Duplicate outbound arrows from `GitLabMonorepo` to `Out_PromptOrch` (L1)

**Lines involved:**
```
GitLabMonorepo --> Out_PromptOrch : "existing v1 code patterns\n(read-only — no invention)\n[AccountController=v1, AccountControllerV2=v2]"
GitLabMonorepo --> Out_PromptOrch : "latest Java version &\nbest practices the project uses"
```

Two separate arrows exist between the same source and destination. PlantUML will render these as two overlapping or adjacent lines, which is visually confusing. More critically, these represent two logically distinct data contracts between the same components. Whether they are separate API calls, separate payload fields, or separate pipeline triggers is entirely undeclared.

---

### Issue 5 — Direct cross-layer skip from L0 → L4, bypassing L1, L2, L3 (L0, L4, overview)

**Elements involved:**
- Overview: `L0 ..> L4 : "spec docs\n(Prompt Orchestrator: ticket creation)"`
- L4: `In_L0_Specs --> PromptOrchestrator : "spec docs\n(ticket creation)"`

Raw Markdown spec docs from L0 flow directly into `PromptOrchestrator` without passing through `RepoDocSync` → `ParsingChunking` → `MetadataEntityExtraction` → `ChunkStore` → graph ingestion. This means the ticket creation use case operates on unprocessed, unchunked, un-version-tagged raw spec text, while the coding assistance use case (Case 1) operates on the fully enriched Neo4j graph. The architectural justification for this difference is not stated.

---

### Issue 6 — Prompt Orchestrator receives both raw L0 specs and enriched L3 graph context for ticket creation (L4)

**Elements involved:**
```
In_L0_Specs --> PromptOrchestrator : "spec docs\n(ticket creation)"
In_Neo4j_PO --> PromptOrchestrator : "project knowledge  (coding assistance)\n/ spec areas  (ticket creation)"
```

Both `In_L0_Specs` (raw Markdown from L0) and `In_Neo4j_PO` (enriched graph context from L3) are labeled as inputs to Prompt Orchestrator for ticket creation ("spec areas"). No merge, deduplication, or selection component is declared between these two inputs. It is unclear whether both are consumed simultaneously per request, used as fallbacks, or serve different sub-cases within Case 3.

---

### Issue 7 — Version tagging disappears inside Layer 2 (L2)

**Elements involved:**
- L1 outputs: `MarkdownSpecs "(v1 + v2)"`, `SpecYAMLFiles "(v1 + v2)"`
- L2 components: `ParsingChunking`, `MetadataEntityExtraction (/ version tag)`, `ChunkStore`, `EmbeddingGeneration`, `RelationshipExtraction`, `GraphConstruction`, `IngestionPipeline`
- L3 input: `In_Ingestion` labeled "enriched nodes, embeddings, relationships"

Version tags (v1/v2/v3) are present on L1 input components and on all L3 output labels/nodes. Inside L2, the only mention of version is the ambiguous `(/ version tag)` annotation on `MetadataEntityExtraction`. No arrow label or component note in L2 confirms that version tags survive through `ChunkStore`, the parallel branches, `GraphConstruction`, or `IngestionPipeline`. The `ChunkStore` label makes no mention of version tagging. Whether version tags are preserved as chunk metadata is undeclared.

---

### Issue 8 — `(/ version tag)` notation in `MetadataEntityExtraction` is ambiguous (L2)

**Element involved:**
```
rectangle "Metadata & Entity\nExtraction  (/ version tag)" as MetadataEntityExtraction
```

The `(/` prefix is not defined anywhere in the L2 legend or notes. It could mean: (a) version tagging is one of the extraction tasks performed here, (b) version tagging is optional, or (c) it is a shorthand for something else. Given that version tagging is architecturally critical (it underpins every L3 capability), this ambiguity in the only component that appears to perform it is a significant gap.

---

### Issue 9 — `Neo4jKG` is a single point of failure with no redundancy annotation (L3)

**Element involved:**
```
rectangle "Neo4j Knowledge Graph\n(unified, multi-version)\n..." as Neo4jKG
```

`Neo4jKG` receives the entire ingestion output via `In_Ingestion --> Neo4jKG` and is the sole provider to all four L4 services. No replica, read replica, cluster member, cache layer, or failover annotation appears anywhere in L3 or in the downstream layer descriptions. Every L4 service (`SemanticSearchAPI`, `GraphQueryService`, `RAGService`, `PromptOrchestrator`) has a hard dependency on this single component. The L3 node label claims "Vector Embeddings · Metadata · Semantic Relationships · Schema Traceability · Cross-Version Diffs · Stakeholder ACLs" — all stored in one unprotected location.

---

### Issue 10 — `Stakeholder ACLs` declared inside `Neo4jKG` label but no enforcement component exists (L3, L4)

**Elements involved:**
- L3: `Neo4jKG` label contains `"Stakeholder ACLs"`
- L4: `AccessControlGateway` description: `"Auth: GitLab / Confluence credentials\nAll inbound & outbound traffic enforced here"`

The `AccessControlGateway` enforces GitLab/Confluence credentials but is documented as controlling *consumer-to-service* traffic (L5 → L4 and L6 → L4). The claim that ACLs are stored in Neo4j implies graph-node-level or relationship-level access control, which is a fundamentally different mechanism from the gateway's credential check. No component in any layer implements, evaluates, or enforces the graph-level Stakeholder ACLs. The ACLs are declared as data (inside the Neo4j node) but never enforced as behavior anywhere in the .puml files.

---

### Issue 11 — No LLM component appears anywhere in the architecture (all layers)

**Elements involved:**
- `RAGService` (L4) — requires a generation step
- `PromptOrchestrator` (L4) — constructs and executes prompts
- `SemanticSearchAPI` (L4) — may require re-ranking or LLM-based scoring
- `IDEExtensions` (L5) — labeled "(hosts GitHub Copilot)" but GitHub Copilot is an external LLM service

No component labeled as an LLM, language model API, inference endpoint, or model provider appears in any of the eight .puml files. RAG architecturally requires retrieval + generation; only the retrieval path is modeled. The `PromptOrchestrator` constructs prompts but never sends them to any component. The IDE Extension is the only place an LLM is implied (GitHub Copilot), but "hosts" is ambiguous — it could mean the extension *embeds* Copilot or merely *runs alongside* it.

---

### Issue 12 — Response arrows use `..>` (async/dashed) while request arrows use `-->` (sync) for the same services (L4)

**Lines involved:**
```
In_L5_Consumers --> AccessControlGateway          (sync request)
AccessControlGateway --> SemanticSearchAPI         (sync)
AccessControlGateway --> GraphQueryService         (sync)
AccessControlGateway --> RAGService               (sync)
AccessControlGateway --> PromptOrchestrator       (sync)

SemanticSearchAPI  ..> AccessControlGateway : "[response]"   (async)
GraphQueryService  ..> AccessControlGateway : "[response]"   (async)
RAGService         ..> AccessControlGateway : "[response]"   (async)
PromptOrchestrator ..> AccessControlGateway : "[response]"   (async)
AccessControlGateway ..> Out_L5_Responses                    (async)
```

The L4 legend explicitly labels `- ->` as "Asynchronous response." If all four services return asynchronous responses, the gateway must implement a callback or polling mechanism rather than blocking HTTP. This has major implementation implications (message queue, WebSocket, server-sent events). No such mechanism is declared. Alternatively, if `..>` was simply chosen to distinguish request from response visually without implying true async, the legend is misleading.

---

### Issue 13 — Ticket creation arrow `PromptOrchestrator --> Out_GitLabIssues` is sync; ticket implementation arrow `PromptOrchestrator ..> Out_PipelineService` is async (L4)

**Lines involved:**
```
PromptOrchestrator --> Out_GitLabIssues    : "new ticket  (To Do column)\n(ticket creation)"
PromptOrchestrator ..> Out_PipelineService : "generated prompt\n(ticket implementation)"
```

Both are outputs of the same `PromptOrchestrator`. Ticket creation (Case 3) is modeled as synchronous (solid arrow); prompt delivery to the Pipeline Service (Case 2) is modeled as async (dashed arrow). No justification for this asymmetry is given. If ticket creation blocks until the GitLab API confirms the ticket was created, the sync choice may be intentional, but it is undeclared. If the async arrow for `Out_PipelineService` implies a message queue or webhook, the transport mechanism is not shown.

---

### Issue 14 — `FutureAIAgents <<placeholder>>` is a dead-end node in L5 (L5)

**Elements involved:**
```
In_Gateway --> FutureAIAgents
```
No outbound arrow from `FutureAIAgents` to any L6 persona, output system, or any other component exists. The node receives input from the gateway but produces no output visible in the diagram. The note says "persona mapping deferred." This means the gateway is already authorizing traffic to an undefined consumer with no declared purpose, scope, or output.

---

### Issue 15 — `SupportOps_p` persona is served by only one consumer (`InternalChatbot`) (L5, L6)

**Elements involved:**
- L5: `InternalChatbot --> Out_SupportOps`
- L6: `In_Chatbot --> SupportOps_p : "serves"`
- L6 note: "Support & Ops" listed in the persona set

No other L5 consumer maps to Support & Ops. The `NoteMapping` in L5 confirms this: "Support & Ops" appears only under Internal Chatbot. Whether this is intentional (Support & Ops only needs a chatbot) or an oversight (e.g., Pipeline Service or Developer Portal is also relevant to ops) is not documented.

---

### Issue 16 — `AccessControlGateway` does not intercept L3 → L4 service data flows (L4)

**Elements involved:**
```
In_Neo4j_SS  --> SemanticSearchAPI
In_Neo4j_GQ  --> GraphQueryService
In_Neo4j_RAG --> RAGService
In_Neo4j_PO  --> PromptOrchestrator
```

The gateway description states: "All inbound & outbound traffic enforced here." However, the four arrows from Neo4j to the services bypass the gateway entirely — they go directly to each service. The gateway only intercepts consumer-originated requests (L5 → gateway → services) and persona requests (L6 → gateway). The data pipeline from the graph into the services is completely outside the gateway's enforcement boundary. This means a compromised service could be fed malicious graph data without any access-control layer in between.

---

### Issue 17 — Labeled output format mismatch between L2 `IngestionPipeline` and L3 `In_Ingestion` (L2, L3)

**Elements involved:**
- L2 output: `IngestionPipeline --> Out_Neo4j` (no label on this arrow)
- L3 input: `In_Ingestion` labeled `"enriched nodes, embeddings, relationships"` (on the L3 external input rectangle)
- L2 components produce: embeddings (from `EmbeddingGeneration`), relationships (from `RelationshipExtraction`), graph nodes (from `GraphConstruction`)

The arrow from `IngestionPipeline` to `Out_Neo4j` in L2 carries no label. The receiving end in L3 is described as `"enriched nodes, embeddings, relationships"`. There is no declared serialization format, wire protocol, or data contract between L2's output and L3's input. The `IngestionPipeline` component absorbs output from `GraphConstruction` but its own output format is undefined. It is not clear whether this represents a direct Neo4j write, a Kafka topic, a REST push, or a file import.

---

### Issue 18 — `GraphConstruction` waits for both parallel branches but no synchronization mechanism is declared (L2)

**Elements involved:**
- `together {}` block containing `EmbeddingGeneration` and `RelationshipExtraction`
- Note: "Graph Construction waits for both branches to complete before writing to Neo4j"

The `together {}` directive in PlantUML controls *layout only* (co-ranks elements visually); it has no semantic meaning about execution order or synchronization. The note declares a join semantics ("waits for both branches") but no barrier, join task, or orchestration component is shown to implement this. Whether this is a future design note or an assumed capability of the pipeline runtime is unstated.

---

### Issue 19 — `In_L1_Code --> PromptOrchestrator` appears twice with different labels (L4)

**Lines involved:**
```
In_L1_Code --> PromptOrchestrator : "existing v1 code patterns\n(read-only, no invention)\n[AccountController=v1, AccountControllerV2=v2]"
In_L1_Code --> PromptOrchestrator : "latest Java version &\nbest practices"
```

Two separate arrows exist from `In_L1_Code` to `PromptOrchestrator`. Same source, same destination, different labels. This mirrors Issue 4 in L1 and repeats the same ambiguity at L4: whether these represent two separate calls, two fields in one payload, or two pipeline stages is undeclared.

---

### Issue 20 — `AccessControlGateway` arrow style is solid (`-->`) for all dispatches to services, but response arrows are dashed (`..>`); the gateway's own output to `Out_L5_Responses` is dashed (L4)

**Lines involved:**
```
AccessControlGateway --> SemanticSearchAPI    (solid)
AccessControlGateway --> GraphQueryService   (solid)
AccessControlGateway --> RAGService          (solid)
AccessControlGateway --> PromptOrchestrator  (solid)
AccessControlGateway ..> Out_L5_Responses    (dashed)
```

The gateway dispatches requests synchronously (solid arrows) but returns responses asynchronously (dashed arrow to `Out_L5_Responses`). If the gateway is a synchronous reverse proxy, both request dispatch and response return should use the same arrow style. If the gateway is a message broker (async dispatch), the inbound request arrows should also be dashed. The mixed style implies an inconsistent gateway pattern without declaring which it is.

---

### Issue 21 — `Cross-Version Diffs` declared in `Neo4jKG` label but no component computes or serves them (L3, all layers)

**Element involved:**
```
"Cross-Version Diffs" in Neo4jKG label
```

No component in L2 (ingestion) or L4 (services) is labeled as computing or exposing cross-version diffs. `GraphQueryService` could theoretically return diff results via Cypher, but this is not labeled. `SemanticSearchAPI` operates on embeddings, not diffs. No API endpoint, scheduled job, or ingestion-time diff component is declared. The capability is asserted as a stored property of the graph but the mechanism that populates it is absent.

---

### Issue 22 — Missing `NoteAudit` arrow destination: audit logs are captured but their destination is explicitly unresolved (L4)

**Element involved:**
```
note as NoteAudit #FFE0E0
  <b>Architecture Decision Required: Audit Log Destination</b>
  The API Gateway captures access and audit events.
  The destination for these audit logs has not yet been
  specified  (e.g. SIEM, centralised log store, Loki).
  No arrow is drawn until this is confirmed.
end note
```

This note is self-documenting, but its consequence is that the security audit trail — the primary evidence for access control compliance — has no destination in the architecture. For a platform exposing regulatory API specs (NextGenPSD2, OpenFinance), the absence of a declared audit log destination is a compliance risk, not merely a design gap.

---

### Issue 23 — Layer 5's `ConfluenceReport` writes to Confluence via `..>` (async) but Layer 4's `PromptOrchestrator --> Out_Confluence` is sync (L4, L5)

**Lines involved:**
- L4: `PromptOrchestrator --> Out_Confluence : "read / write / edit"` (solid, sync)
- L5: `ConfluenceReport ..> Out_Confluence : "write report"` (dashed, async)
- L6: `In_PromptOrch --> adorsysConfluence : "read / write / edit"` (solid)
- L6: `In_ConfReport_Push ..> adorsysConfluence : "write report\n(scheduled push)"` (dashed)

Two different components write to the same `adorsysConfluence` destination using different arrow styles (sync vs. async). This means Confluence receives both synchronous (real-time) writes from the Prompt Orchestrator and asynchronous (scheduled) writes from the Confluence Report. No locking, conflict resolution, or page-namespace separation is declared to prevent concurrent write collisions on the same Confluence pages.

---

## 3. Open Questions (No Assumptions Rule)

- **Q-1** Does the `BerlinGroup_v1 ..> GitLab_ngpsd2 : "hosts YAML repo"` dotted arrow intentionally mean the YAML repository access is async or planned, or was `..>` chosen to represent an external structural dependency? The answer determines whether v1 YAML acquisition is currently operational.

- **Q-2** Is `GitLab_of --> YAML_v2 : "pull-p"` a typo for `"pull"`, or does the `-p` suffix carry a specific meaning (e.g., "planned", "partial", "pull with parameters")? If planned, is v2 YAML acquisition not yet built?

- **Q-3** What is the expected timeline and source for v3 spec acquisition? The `L0_v3` package is empty, but `Neo4jKG` in L3 already claims v3 tagging. Is v3 data expected to flow through the same L0→L1→L2→L3 pipeline once the source is published, and if so, does this require any architecture changes?

- **Q-4** What is the intended semantic of the duplicate arrows between the same source and destination components (Issues 4 and 19)? Are these separate API calls, separate payload fields, separate pipeline stages, or separate trigger events?

- **Q-5** Is Layer 1 a persistent data store (with versioning and history) or a transient staging area (contents deleted after ingestion)? This affects idempotency of the Layer 2 pipeline and the ability to replay ingestion without re-fetching from external sources.

- **Q-6** What is the data sensitivity and residency requirement for the spec documents and code patterns? Specifically, must embedding generation (`EmbeddingGeneration` in L2) and LLM inference (`RAGService`, `PromptOrchestrator` in L4) use on-premises/air-gapped models, or are external API calls to OpenAI/Cohere/Anthropic permissible?

- **Q-7** What is the required availability and durability SLA for `Neo4jKG`? This determines whether a standalone instance, a causal cluster (Neo4j Enterprise), or a managed service (AuraDB) is appropriate.

- **Q-8** What is the expected query interface for `GraphQueryService`? Allowing raw Cypher from consumers is a Cypher injection risk; a parameterized query layer changes the implementation significantly.

- **Q-9** What enterprise messaging platform does adorsys use? The `InternalChatbot` serves five distinct persona types; whether it is deployed as a Slack app, Teams bot, or standalone web UI changes the consumer interface and authentication integration requirements.

- **Q-10** What is the intended purpose and scope of `ArchitectureAssistant` (L5) that distinguishes it from `InternalChatbot`? Both serve Architects and Product Managers. The .puml provides no description, note, or differentiating label.

- **Q-11** Which LLM(s) or inference provider(s) does the platform intend to use? No LLM component appears anywhere in the eight .puml files (see Issue 11). `RAGService` and `PromptOrchestrator` require a generation step; its provider, API contract, latency budget, and cost model are entirely unspecified.

- **Q-12** Are the `..>` (async) response arrows in L4 (Issue 12) intentional, implying a non-blocking gateway with a message queue or callback mechanism? Or were they chosen purely for visual distinction between requests and responses, with no async semantics intended?

- **Q-13** What is the Audit Log destination for the `AccessControlGateway`? The `NoteAudit` in L4 explicitly flags this as an open architecture decision. Are there compliance requirements (e.g., PSD2 audit trail obligations) that constrain the answer?

- **Q-14** How is the `Stakeholder ACLs` property in `Neo4jKG` (L3) enforced at query time? Is access control expected to be implemented at the graph database level (Neo4j role-based security), at the service level (each L4 service filters results by caller identity), or at the gateway level (request scope limits)?

- **Q-15** What triggers the `PipelineService` (L5) to initiate the ticket-implementation flow (Case 2)? The diagram shows `GitLabIssuesBoard --> PipelineService : "ticket description"` but the trigger condition (e.g., issue label change, GitLab CI webhook, scheduled job) is not declared.

- **Q-16** What expected data volumes (documents ingested per run, query throughput, concurrent users) are anticipated? Without this, it is not possible to size Neo4j, choose an embedding batch strategy, or determine whether the API Gateway needs rate limiting.

- **Q-17** Is this a greenfield build or does existing infrastructure already exist for any layer? The .puml mentions GitLab as an existing monorepo and adorsys Confluence as an existing system, but whether any ingestion tooling, Neo4j instance, or API layer already exists is not stated, and this affects the build-vs-integrate decision for every Layer 2 and Layer 4 component.

- **Q-18** What prevents concurrent writes from `PromptOrchestrator` (sync) and `ConfluenceReport` (async/scheduled) from conflicting on the same Confluence pages? Is there a page-namespace convention, a write lock, or a coordination mechanism intended but not yet modeled?

- **Q-19** What is the intended deployment target for this platform? The .puml is cloud-provider-agnostic and on-premises-agnostic. The choice of Kubernetes vs. PaaS vs. bare metal affects the operationalization of every component and is not answerable from the .puml files.

- **Q-20** Is `FutureAIAgents <<placeholder>>` already being routed through the API Gateway (`In_Gateway --> FutureAIAgents`)? If so, what authorization scope is the gateway granting to an undefined consumer, and should this arrow exist before the agent's purpose and persona mapping are determined?
