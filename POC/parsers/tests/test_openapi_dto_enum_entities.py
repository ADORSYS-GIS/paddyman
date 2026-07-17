"""Integration tests for DTO/Enum entity extraction in OpenAPI output."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from parsers.openapi_file_output import write_openapi_file_normalized_jsons


def _render_payload(tmp_path: Path, spec_content: str) -> dict:
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir(parents=True)
    (spec_dir / "payment.yaml").write_text(spec_content, encoding="utf-8")
    output_dir = tmp_path / "output"
    paths = write_openapi_file_normalized_jsons(source_dir=spec_dir, output_dir=output_dir)
    return json.loads(paths[0].read_text(encoding="utf-8"))


def test_extracts_dto_enum_and_simple_schema_entities(tmp_path: Path) -> None:
    payload = _render_payload(
        tmp_path,
        """openapi: 3.0.1
info:
  title: Payment API
  version: 1.0.0
paths: {}
components:
  schemas:
    PaymentInitiation:
      type: object
      required: [amount]
      properties:
        amount:
          type: number
        remittance:
          type: string
    PaymentProduct:
      type: string
      enum: [sepa, instant]
    Bic:
      type: string
""",
    )

    entities = payload["entities"]
    assert len([e for e in entities if e["type"] == "DTO"]) == 1
    assert len([e for e in entities if e["type"] == "Enum"]) == 1
    assert any(e["type"] == "Schema" and e["name"] == "Bic" for e in entities)

    dto = next(e for e in entities if e["type"] == "DTO")
    enum_entity = next(e for e in entities if e["type"] == "Enum")
    assert dto["properties"]["required_fields"] == ["amount"]
    assert dto["properties"]["property_count"] == 2
    assert enum_entity["properties"]["values"] == ["sepa", "instant"]
    assert enum_entity["properties"]["value_count"] == 2


def test_creates_has_property_and_has_enum_value_relationships(tmp_path: Path) -> None:
    payload = _render_payload(
        tmp_path,
        """openapi: 3.0.1
info:
  title: Payment API
  version: 1.0.0
paths: {}
components:
  schemas:
    PaymentInitiation:
      type: object
      required: [amount]
      properties:
        amount:
          type: number
        remittance:
          type: string
    PaymentProduct:
      type: string
      enum: [sepa, instant]
""",
    )

    relationships = payload["relationships"]
    has_property = [r for r in relationships if r["type"] == "HAS_PROPERTY"]
    has_enum_value = [r for r in relationships if r["type"] == "HAS_ENUM_VALUE"]

    assert len(has_property) == 2
    assert len(has_enum_value) == 2
    assert any(r["properties"]["property_name"] == "amount" for r in has_property)
    assert any(r["properties"]["value"] == "instant" for r in has_enum_value)
