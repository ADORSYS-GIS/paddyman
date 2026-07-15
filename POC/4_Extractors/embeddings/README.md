# Embedding Generator (`3_Extractors/embeddings`)

Generates vector embeddings for extracted entities and normalized document chunks.
Supports any OpenAI-compatible embedding provider; no code changes are required
to switch providers.

The embedding stage consumes extraction outputs only. It does not read raw Java,
OpenAPI, Markdown, or parser-specific artifacts.

## Architecture

```
client/          — Provider abstraction (BaseEmbeddingClient, OpenAICompatEmbeddingClient, factory)
models/          — Output models (EmbeddingResult, EmbeddingMetadata, EmbeddingInputType)
services/        — Orchestration + retry logic (EmbeddingService, BatchEmbeddingService)
pipeline.py      — Stage 5 runner over extraction JSON/JSONL artifacts
tests/           — Unit tests (pytest)
```

## Provider Abstraction

All embedding calls go through `BaseEmbeddingClient`.  The only concrete
implementation is `OpenAICompatEmbeddingClient`, which wraps the `openai` SDK
with a configurable `base_url`.  Swap providers by pointing `EMBED_BASE_URL`,
`EMBED_MODEL_NAME`, and `EMBED_API_KEY` at any OpenAI-compatible endpoint.

To add a new provider, implement `BaseEmbeddingClient.embed()`,
`embed_batch()`, `model`, and `provider_name` — nothing else changes.

## Configuration

All settings are loaded through `shared.config.settings`.
Non-sensitive values live in `POC/config.yml`; secrets live in `POC/.env`.

| Config key | Source | Description |
|---|---|---|
| `embedding.base_url` | `config.yml` | Provider base URL |
| `embedding.model_name` | `config.yml` | Embedding model identifier |
| `EMBED_API_KEY` | `.env` | API key |
| `embedding.timeout` | `config.yml` | HTTP timeout in seconds |
| `embedding.max_retries` | `config.yml` | Retry attempts on failure |
| `embedding.batch_size` | `config.yml` | Max texts per batch request |

## Supported Embedding Types

| `EmbeddingInputType`  | Source                          |
|-----------------------|---------------------------------|
| `entity`              | Any generic extracted entity    |
| `chunk`               | Generic parsed document chunk   |
| `java_class`          | Extracted Java-derived class    |
| `java_method`         | Extracted Java-derived method   |
| `openapi_schema`      | Extracted OpenAPI-derived schema |
| `api_endpoint`        | Extracted API endpoint          |
| `markdown_section`    | Extracted document section      |

## Running

```bash
cd POC
PYTHONPATH=.:4_Extractors python3 -m embeddings.pipeline
```

## Output Format

```json
{
  "entity": "PaymentService",
  "input_type": "java_class",
  "source_id": "aspsp-xs2a",
  "vector": [0.12, -0.34, ...],
  "metadata": {
    "embedding_model": "qwen3-embedding-8b",
    "embedding_provider": "openai_compat",
    "vector_dimension": 4096,
    "source_parser": "java_parser",
    "repository": "aspsp-xs2a",
    "module": "payments",
    "file_path": "/src/PaymentService.java",
    "version_tag": "2"
  }
}
```

## Running Tests

```bash
cd POC/3_Extractors/embeddings
../../.venv/bin/python -m pytest
```

All tests are pure unit tests; no live API calls are made (the embedding
client is mocked).
