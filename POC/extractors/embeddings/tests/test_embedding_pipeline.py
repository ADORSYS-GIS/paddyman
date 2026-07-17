"""Tests for the embedding stage runner."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

_POC_ROOT = Path(__file__).resolve().parents[3]
_EXTRACTORS_ROOT = _POC_ROOT / "4_Extractors"
for _path in (str(_POC_ROOT), str(_EXTRACTORS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from embeddings.pipeline import run_pipeline


def test_embedding_pipeline_consumes_extraction_outputs(tmp_path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    record = {
        "source_id": "doc-1",
        "source_parser": "markdown_parser",
        "spacy_entities": [{"type": "concept", "name": "Payment", "source": "doc-1"}],
        "document_chunks": [{"text": "Payment initiation", "label": "doc-1"}],
    }
    (input_dir / "extraction.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")

    response = MagicMock()
    response.vector = [0.1, 0.2]
    response.input_type = "entity"
    response.entity = "Payment"
    service = MagicMock()
    service.embed_entities.return_value = [response]
    service.embed_chunks.return_value = [response]

    output_path = run_pipeline(input_dir, output_dir, service)

    assert output_path is not None
    payload = json.loads(output_path.read_text(encoding="utf-8").splitlines()[0])
    assert payload["entity_embeddings"][0]["dimension"] == 2
    assert payload["chunk_embeddings"][0]["dimension"] == 2