"""Integration tests for Operation and Tag entities in OpenAPI output."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from openapi_file_output import write_openapi_file_normalized_jsons


def _render_payload(tmp_path: Path, spec_content: str) -> dict:
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir(parents=True)
    (spec_dir / "payment.yaml").write_text(spec_content, encoding="utf-8")
    output_dir = tmp_path / "output"
    paths = write_openapi_file_normalized_jsons(source_dir=spec_dir, output_dir=output_dir)
    return json.loads(paths[0].read_text(encoding="utf-8"))


def test_creates_operation_and_tag_entities_with_relationships(tmp_path: Path) -> None:
    payload = _render_payload(
        tmp_path,
        """openapi: 3.0.1
info:
  title: Payment API
  version: 1.0.0
paths:
  /payments:
    post:
      operationId: createPayment
      tags: [payments, pis]
      responses:
        '201':
          description: Created
""",
    )

    entities = payload["entities"]
    endpoint = next(e for e in entities if e["type"] == "Endpoint")
    operation = next(e for e in entities if e["type"] == "Operation")
    tags = [e for e in entities if e["type"] == "Tag"]

    assert "operation_id" not in endpoint
    assert endpoint["operation_match_key"] == operation["match_key"]
    assert operation["properties"]["operation_id"] == "createPayment"
    assert {tag["name"] for tag in tags} == {"payments", "pis"}

    rels = payload["relationships"]
    assert any(rel["type"] == "IMPLEMENTS_OPERATION" for rel in rels)
    assert any(rel["type"] == "TAGGED_AS" for rel in rels)


def test_generates_placeholder_operation_id_and_unique_tags(tmp_path: Path) -> None:
    payload = _render_payload(
        tmp_path,
        """openapi: 3.0.1
info:
  title: Demo API
  version: 1.0.0
paths:
  /accounts:
    get:
      tags: [shared]
      responses:
        '200':
          description: ok
  /accounts/{id}:
    get:
      tags: [shared]
      responses:
        '200':
          description: ok
""",
    )

    operations = [e for e in payload["entities"] if e["type"] == "Operation"]
    tags = [e for e in payload["entities"] if e["type"] == "Tag"]

    operation_ids = [e["properties"]["operation_id"] for e in operations]
    assert len(operation_ids) == len(set(operation_ids))
    assert all(op_id for op_id in operation_ids)
    assert len(tags) == 1
