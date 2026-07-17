# LLM Extractor (`3_Extractors/llm`)

LLM-based structured entity and relationship extraction. Sends chunked text to an
OpenAI-compatible API and parses the structured JSON response into `ExtractionResult`
objects shared across the pipeline.

## Architecture

```
client/          — Provider abstraction (BaseLLMClient, OpenAICompatClient, factory)
prompts/         — Prompt construction (build_request)
parser/          — JSON response parsing (ResponseParser)
services/        — Orchestration + retry logic (ExtractionService)
tests/           — Unit tests (pytest)
```

## Provider Abstraction

All LLM calls go through `BaseLLMClient`. The only concrete implementation is
`OpenAICompatClient`, which wraps the `openai` SDK with a configurable `base_url`.
Swap providers by changing `llm.base_url` and `llm.model` in `POC/config.yml` for any OpenAI-compatible
endpoint (OpenAI, OpenRouter, Azure OpenAI, local Ollama, or any compatible provider).

## Configuration

All settings are read through `shared.config.settings`.
Non-sensitive values live in `POC/config.yml`; secrets live in `POC/.env`.

| Variable          | Default                                  | Description                  |
|-------------------|------------------------------------------|------------------------------|
| Config key | Source | Description |
|---|---|---|
| `llm.base_url` | `config.yml` | Provider base URL |
| `llm.model` | `config.yml` | Model identifier |
| `LLM_API_KEY` | `.env` | API key |
| `llm.timeout` | `config.yml` | HTTP timeout in seconds |
| `llm.max_retries` | `config.yml` | Retry attempts on failure |
| `llm.temperature` | `config.yml` | Sampling temperature |
| `llm.max_tokens` | `config.yml` | Max tokens per response |

## Input / Output

**Input**: plain text produced by any upstream parser (`java_parser`, `openapi_parser`,
`markdown_parser`) plus a `SourceMetadata` object identifying the source document.

**Output**: `ExtractionResult` with:
- `entities` — list of `Entity` objects; each has `properties["extraction_rule"] = "llm"`
  and `properties["source_parser"]` indicating which parser produced the text.
- `relationships` — list of `Relationship` objects with `confidence` clamped to [0, 1].
- `status` — `SUCCESS` (≥1 entity), `PARTIAL` (0 entities), or `FAILED` (parse error /
  all retries exhausted).
- `errors` / `warnings` — diagnostic messages for downstream observability.

## Running Tests

```bash
cd POC/3_Extractors/llm
../../.venv/bin/python -m pytest
```

All tests are pure unit tests; no live API calls are made (the LLM client is mocked).
