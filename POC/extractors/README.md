# Entity Extraction Pipeline (`3_Extractors`)

Phase 4 pipeline: runs rule-based and GLM extraction over the normalized JSON produced by the parser pipeline.

## Pipeline Stages

1. **Load normalized JSON** — reads `settings.extraction_input_dir`
2. **spaCy rule-based extraction** — vocabulary matching + version-tag injection (3-priority chain)
3. **GLM structured extraction** — LLM entity/relationship extraction via OpenAI-compatible API
4. **Triple generation** — RDF-style `(subject, predicate, object)` records from GLM output
5. **Output writing** — entities, relationships, triples, version tags, and document chunks

## Required Input

- `settings.extraction_input_dir`
- Expected files: `java_openapi_markdown_parser_output.json`, `java_code/*.json`, `openapi_specs/*.json`, or `markdown_parser_output.json`
- No extractor consumes Java, OpenAPI, or Markdown parser-specific outputs directly.

## Sub-modules

| Module | Purpose |
|--------|---------|
| `spacy/` | Rule-based entity extraction + version tagger |
| `llm/` | LLM structured extraction + triple builder |
| `embeddings/` | Stage 5 embedding generation over extraction outputs |
| `loader.py` | Converts normalized JSON documents to extraction records |
| `pipeline.py` | Orchestrates all extraction stages |
| `main.py` | CLI entry point |

## How to Run

```bash
cd POC/3_Extractors
../.venv/bin/python main.py
```

Configuration:

- `POC/config.yml` contains provider URLs, model names, paths, limits, and feature settings.
- `POC/.env` contains secrets only, such as `LLM_API_KEY` and `EMBED_API_KEY`.
- Code reads both through `shared.config.settings`; typed fields cover common values, while `settings.get(...)`, `settings.raw`, and `settings.env` expose the full autoloaded sources.

## Output Summary

```
Records processed   : 42
spaCy entities      : 178
GLM entities        : 63
Relationships       : 21
Triples             : 19
Entity embeddings   : 0
Chunk embeddings    : 0
Failures            : 0
```

## Running Tests

```bash
# Module tests
cd POC/3_Extractors/spacy   && ../../.venv/bin/python -m pytest
cd POC/3_Extractors/llm     && ../../.venv/bin/python -m pytest
cd POC/3_Extractors/embeddings && ../../.venv/bin/python -m pytest

# Integration tests
cd POC && .venv/bin/python -m pytest tests/test_extractor_pipeline.py
```
