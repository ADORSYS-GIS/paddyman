Across all of your implementation prompts, you've gradually built a consistent engineering standard. Rather than repeating the same instructions in every prompt, you can define them once as **Global Implementation Standards** and have every future prompt inherit them.

---

# Global Implementation Standards

Every implementation must follow the standards below unless explicitly stated otherwise.

## Architecture

* Follow SOLID principles.
* Follow DRY.
* Follow KISS.
* Follow Separation of Concerns.
* Keep modules cohesive and loosely coupled.
* Prefer composition over inheritance.
* Design for extensibility.
* Avoid premature abstraction.
* Avoid code duplication.

---

## Code Organization

* No Python source file may exceed **150 LOC**.
* Keep classes and functions focused on a single responsibility.
* Split large implementations into small modules.
* Keep directory structure clean and consistent.
* Reuse existing shared infrastructure whenever possible.
* Do not duplicate existing functionality.

---

## Typing

* Use Python type hints throughout.
* Use dataclasses or Pydantic models where appropriate.
* Avoid untyped public APIs.

---

## Configuration

* Never hardcode:

    * paths
    * URLs
    * repository lists
    * schedules
    * output directories
    * credentials
    * parser behavior

* Read configuration exclusively from `shared.config`:

    ```python
    from shared.config import settings
    ```

* Never call `os.environ` directly outside `POC/shared/config/`.

* Configuration values must originate from `POC/.env`.

* `POC/.env.example` is the single authoritative template for all environment variables.

* New configuration values require both a field in `shared/config/settings.py` and a documented entry in `POC/.env.example`.

---

## Error Handling

* Fail gracefully.
* Continue processing whenever possible.
* Record recoverable failures.
* Raise meaningful custom exceptions.
* Never silently swallow exceptions.
* Produce actionable error messages.

---

## Logging

* Use structured logging.
* Log meaningful events.
* Avoid excessive logging.
* Never log secrets or credentials.

---

## Testing

Every implementation must include unit tests covering:

* happy paths
* edge cases
* invalid inputs
* empty inputs
* deterministic behavior
* error handling

Tests should be deterministic and independent.

---

## Documentation

Update the relevant README when implementation changes.

Documentation should:

* use concise bullet points
* explain purpose
* explain configuration
* explain outputs
* explain how to test
* avoid unnecessary prose
* avoid documenting internal implementation details
* avoid project structure diagrams unless explicitly requested

---

## Idempotency

Implementations should be idempotent whenever applicable.

Examples:

* avoid downloading existing artifacts
* avoid cloning existing repositories
* avoid regenerating existing outputs unless configured
* avoid duplicate processing

---

## Extensibility

Design components so new implementations can be added with minimal code changes.

Prefer:

* registries
* factories
* configuration-driven behavior
* plugin-like architecture

Avoid switch statements and hardcoded branching.

---

## Determinism

Outputs must be deterministic.

Examples:

* deterministic ordering
* stable identifiers
* reproducible execution
* predictable outputs

---

## Performance

Avoid unnecessary work.

Examples:

* avoid rescanning unchanged files
* avoid repeated downloads
* avoid repeated cloning
* stream large files when appropriate
* avoid loading unnecessary data into memory

---

## Parser Principles

Parsers should:

* have one responsibility
* never perform graph construction
* never perform persistence unless explicitly required
* produce only the Intermediate Representation (IR)
* remain independent of downstream consumers

---

## Extractor Principles

Extractors should:

* only discover source files
* never parse contents
* never build entities
* never construct graphs

---

## Intermediate Representation (IR)

All parser outputs should use the common IR.

The IR should remain parser-agnostic and act as the contract between parsing and graph construction.

---

## Separation of Pipeline Stages

Keep responsibilities strictly separated.

```
Discovery
    ↓
Parsing
    ↓
Intermediate Representation (IR)
    ↓
Normalization
    ↓
Graph Construction
```

Each stage should depend only on the previous stage.

---

## Configuration-Driven Design

Behavior should be configurable rather than hardcoded.

Examples include:

* source directories
* repository URLs
* output directories
* schedules
* enabled parsers
* enabled extractors
* download locations
* parser options

---

## Acceptance Criteria

Every implementation prompt should define clear acceptance criteria.

Implementation is complete only when:

* functionality matches the scope
* tests pass
* documentation is updated
* configuration is respected
* no out-of-scope functionality is introduced

---

I would also add two more standards because they become increasingly valuable as you move toward the Neo4j knowledge graph.

### Dependency Injection

* Components should receive dependencies via constructors or factories.
* Avoid global state.
* Avoid directly instantiating dependencies inside business logic.
* Favor interfaces or abstract base classes where appropriate.

### Domain-Driven Design

Organize code around domain concepts rather than technical concerns.

For example:

```
Parser
Extractor
IR
Normalizer
GraphBuilder
```

instead of generic names like:

```
utils.py
helpers.py
common.py
misc.py
```

---

## Project-wide Environment and Dependency Management

All pipeline components — `1_Get_Resources`, `2_Parsers`, `3_Extractors`,
`4_Graph_Normalisation`, `shared`, and `tests` — are parts of **one
application**, not independent applications.

They share dependencies, configuration, runtime environment, and
infrastructure definitions.

The following resources must exist exactly once at the project root:

```
POC/
├── .venv/
├── requirements.txt
├── docker-compose.yml
└── .env.example
```

Do not create module-level equivalents of any of these files.

---

### Single Virtual Environment

Use the one virtual environment at `POC/.venv/` for all modules.

Do not create `.venv/` directories inside:

* `1_Get_Resources/`
* `2_Parsers/`
* `3_Extractors/`
* `4_Graph_Normalisation/`
* `shared/`
* `tests/`

Run all Python scripts, tests, and tools from the root environment:

```
POC/.venv/bin/python   ...
POC/.venv/bin/pytest   ...
POC/.venv/bin/pip      ...
```

Benefits:

* consistent dependency versions across all stages
* simpler developer workflow — one environment to activate
* straightforward CI/CD integration
* eliminates environment-specific bugs caused by version drift

---

### Single Requirements File

Maintain exactly one dependency definition at `POC/requirements.txt`.

Do not create:

```
1_Get_Resources/requirements.txt
2_Parsers/requirements.txt
3_Extractors/requirements.txt
4_Graph_Normalisation/requirements.txt
```

When implementing a new feature:

* check `POC/requirements.txt` first — the dependency may already be present
* add new dependencies to `POC/requirements.txt` only
* group dependencies logically, for example:

```
# Core
...

# Configuration
...

# Data processing
...

# Graph
...

# Testing
...
```

---

### Single Docker Compose Definition

Maintain exactly one Docker Compose file at `POC/docker-compose.yml`.

Do not create module-specific compose files:

```
# Prohibited
1_Get_Resources/docker-compose.yml
2_Parsers/docker-compose.yml
3_Extractors/docker-compose.yml
```

When a new implementation requires an infrastructure service:

1. Add the service to `POC/docker-compose.yml`.
2. Update `POC/.env.example` with any new variables the service needs.
3. Verify compatibility with existing services before merging.

---

### Single Environment Configuration

Maintain exactly one environment template at `POC/.env.example`.

All configuration must flow through:

```
POC/.env.example
        ↓
shared/config/settings.py
        ↓
all project modules
```

Rules:

* No module-specific `.env` or `.env.example` files.
* No duplicated environment variable definitions.
* Modules must not load environment files directly — import from `shared.config` instead.

New environment variables must be:

* defined in `POC/.env.example` with a descriptive comment
* added to `POC/shared/config/settings.py` with a typed field and sensible default
* consumed via `from shared.config import settings`

---

### Implementation Checklist for Future Tasks

Before every implementation task, verify:

| Concern | Rule |
|---|---|
| Python dependencies | Add to `POC/requirements.txt` only |
| Configuration | Add field to `shared/config/settings.py`; document in `POC/.env.example` |
| Infrastructure | Add service to `POC/docker-compose.yml` only |
| Runtime environment | Use `POC/.venv/`; do not create a new one |
| Environment variables | Load via `from shared.config import settings`; never call `os.environ` directly outside `shared/config/` |

---

### Migration Guidance

If a module is found to contain duplicated environment or dependency files,
the corrective refactoring task must:

* merge dependencies into `POC/requirements.txt` and remove the module-level file
* delete module-level `.venv/` directories
* merge compose service definitions into `POC/docker-compose.yml`
* migrate environment variables into `POC/.env.example` and `POC/shared/config/settings.py`
* replace any direct `os.environ` calls with imports from `shared.config`

---

## Unit Test Co-location

Unit tests belong to the module they test.

Each module must have its own `tests/` directory:

```
1_Get_Resources/
    tests/

2_Parsers/
    tests/

3_Extractors/
    tests/

4_Graph_Normalisation/
    tests/

shared/
    tests/
```

Rules:

* Place module unit tests inside the module's own `tests/` directory.
* Do not place module-specific unit tests in `POC/tests/`.
* `POC/tests/` is reserved exclusively for:
  * Integration tests
  * End-to-end tests
  * Cross-module workflow tests

Benefits:

* Clear ownership — tests live next to the code they verify.
* Independent testability — each module can be tested in isolation.
* Clean separation between unit tests and integration/e2e tests.

---

## Dockerfile Ownership

Each independently runnable module owns its own `Dockerfile`.

```
1_Get_Resources/
    1_Get_Resources/DownloadTrigger/
        Dockerfile

2_Parsers/
    Dockerfile

3_Extractors/
    Dockerfile

4_Graph_Normalisation/
    Dockerfile
```

Rules:

* Each `Dockerfile` builds only its own module.
* The root `POC/docker-compose.yml` orchestrates all module `Dockerfile`s.
* Do not create module-specific `docker-compose.yml` files — use the root compose file only.

---

## README Structure

Documentation must have a single source of truth.

**`POC/README.md`** is the project entry point. It contains:

* Project overview
* Architecture summary
* Quick start instructions
* Links to module READMEs

**Module READMEs** contain module-specific documentation:

* Module purpose and responsibility
* Module workflow
* Inputs and outputs
* Examples
* Development notes

Rules:

* The root README references module READMEs — it does not duplicate their content.
* Setup, configuration, and usage instructions exist only in the appropriate README.
* Avoid repeating the same instructions in multiple places.
* If content belongs to both root and module, it lives in the module README; the root README links to it.