# spaCy Entity Extraction Pipeline — Phase 4

Rule-based entity extraction with deterministic version-tag injection.
Operates on parser outputs from `POC/DataSource/` regardless of which upstream
parser produced them (Java, Markdown, OpenAPI).

---

## Pipeline Architecture

```
Parser Output
      │
      ▼
domain_entity_ruler        vocabulary-based entity matching (EntityRuler)
      │
      ▼
content_version_extractor  regex-based version detection from text
      │
      ▼
version_tagger             3-priority version injection + source labelling
      │
      ▼
Entity Output              shared.models.Entity list
```

---

## Components

| Component | File | Role |
|---|---|---|
| `domain_entity_ruler` | `matcher/entity_matcher.py` | Matches domain terms to `DOMAIN_ENTITY` spans |
| `content_version_extractor` | `version/content_extractor.py` | Detects version strings in text (psd2, berlin_group, openapi, …) |
| `version_tagger` | `pipeline/version_tagger.py` | Injects version + `version_source` using 3-level priority chain |
| `SpacyExtractionPipeline` | `pipeline/pipeline.py` | Orchestrates the full pipeline; exposes `run()` |
| `doc_to_entities` | `pipeline/converter.py` | Converts spaCy Doc → `shared.models.Entity` list |

### Version Priority Chain

1. **Metadata** — explicit `version` / `api_version` field from parser output (`version_source: "metadata"`)
2. **Source path** — structural pattern in `file_path`, `module`, or `repository` (`version_source: "source_path"`)
3. **Content** — first regex match in document text (`version_source: "content:<rule>"`)

---

## Domain Vocabulary

Defined in `vocabulary/vocabulary.py` as `DOMAIN_ENTRIES`. Initial terms:
`Payment`, `Account`, `Consent`, `Customer`, `Transaction`.

Extend by appending a `VocabularyEntry` to `DOMAIN_ENTRIES` — no other file changes required.

---

## Content Version Rules

Defined in `version/rules.py` as `CONTENT_RULES`. Rules applied in priority order:

| Rule | Example match |
|---|---|
| `psd2` | `PSD2 v1.3.16` |
| `berlin_group` | `Berlin Group V2` |
| `nextgenpsd2` | `NextGenPSD2 1.3` |
| `openapi` | `openapi: 3.0.1` |
| `version_prefix_semantic` | `v1.3.16` |
| `version_prefix_major` | `V2` |
| `semantic_version` | `1.3.16` |

Extend by appending a `VersionRule` entry — no other file changes required.

---

## Entity Output Shape

```python
Entity(
    type="entity",
    name="Payment",
    source="aspsp-xs2a",
    properties={
        "label": "DOMAIN_ENTITY",
        "version": "v1.3.16",
        "version_source": "content:psd2",
        "source_parser": "openapi_parser",
        "repository": "aspsp-xs2a",
        "module": "payments",
        "file_path": "/repo/v1/payments.yaml",
        "document": "payments.yaml",
        "confidence": 1.0,
        "extraction_rule": "entity_ruler",
    }
)
```

---

## Usage

```python
from pipeline.pipeline import SpacyExtractionPipeline
from shared.models import SourceMetadata, SourceType

pipeline = SpacyExtractionPipeline.build()

source = SourceMetadata(
    source_id="aspsp-xs2a",
    source_type=SourceType.DOCUMENT,
    location="/repo/v2/consent.md",
    metadata={"repository": "aspsp-xs2a", "version": "2"},
)

result = pipeline.run(
    text="Payment consent was approved.",
    source_metadata=source,
    source_parser="markdown_parser",
)
# result.entities → [Entity(name="Payment", ...), Entity(name="consent", ...)]
```

---

## Adding Future Extractors (Phase 4 Chunks)

Register a new component via the registry — no modifications to existing files:

```python
from pipeline.registry import register_component
from spacy.language import Language

@register_component("my_extractor")
def _add(nlp: Language) -> Language:
    nlp.add_pipe("my_spacy_factory_name")
    return nlp
```

The component is appended after `version_tagger` in every pipeline built
after the registration module is imported.

---

## Running Tests

```bash
cd POC/3_Extractors/spacy
pytest
```
