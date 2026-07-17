"""Tests for OpenAPI parser `$ref` resolution index emission."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[3]
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from parsers.openapi_file_output import write_openapi_file_normalized_jsons


def _render_payload(tmp_path: Path, spec_content: str) -> dict:
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir(parents=True)
    (spec_dir / "petstore.yaml").write_text(spec_content, encoding="utf-8")
    output_dir = tmp_path / "output"
    paths = write_openapi_file_normalized_jsons(source_dir=spec_dir, output_dir=output_dir)
    return json.loads(paths[0].read_text(encoding="utf-8"))


def test_openapi_refs_index_includes_schema_mapping(tmp_path: Path) -> None:
    payload = _render_payload(
        tmp_path,
        """openapi: 3.0.1
info:
  title: Pet API
  version: 1.0.0
paths:
  /pets:
    get:
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Pet'
components:
  schemas:
    Pet:
      type: object
      properties:
        name:
          type: string
""",
    )

    assert "parser_indices" in payload
    indices = payload["parser_indices"]
    assert "openapi_refs" in indices
    refs = indices["openapi_refs"]
    assert "#/components/schemas/Pet" in refs

    pet_id = refs["#/components/schemas/Pet"]
    assert isinstance(pet_id, str) and pet_id

    # Ensure the mapped id resolves to an emitted Schema/DTO/Enum entity
    entities = payload["entities"]
    matches = [e for e in entities if e.get("id") == pet_id]
    assert matches, f"No entity found for id {pet_id}"
    assert matches[0]["type"] in {"DTO", "Schema", "Enum"}
