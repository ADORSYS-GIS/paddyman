"""Tests that OpenAPI parser emits Schema/DTO/Enum and SecurityScheme entities
and that parser_indices.openapi_refs maps schema $ref strings to emitted ids.
"""
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
    (spec_dir / "api.yaml").write_text(spec_content, encoding="utf-8")
    output_dir = tmp_path / "output"
    paths = write_openapi_file_normalized_jsons(source_dir=spec_dir, output_dir=output_dir)
    return json.loads(paths[0].read_text(encoding="utf-8"))


def test_schemas_and_security_emitted_and_indexed(tmp_path: Path) -> None:
    payload = _render_payload(
        tmp_path,
        """openapi: 3.0.1
info:
  title: Pet API
  version: 1.0.0
components:
  schemas:
    Pet:
      type: object
      required: [id, name]
      properties:
        id:
          type: string
        name:
          type: string
    Error:
      type: object
      properties:
        code:
          type: integer
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
paths:
  /pets:
    get:
      security:
        - BearerAuth: []
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Pet'
        '400':
          description: Bad
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
""",
    )

    # parser_indices must include mapping for schemas
    assert "parser_indices" in payload
    refs = payload["parser_indices"].get("openapi_refs")
    assert isinstance(refs, dict)
    assert "#/components/schemas/Pet" in refs
    assert "#/components/schemas/Error" in refs

    pet_id = refs["#/components/schemas/Pet"]
    err_id = refs["#/components/schemas/Error"]
    assert isinstance(pet_id, str) and pet_id
    assert isinstance(err_id, str) and err_id

    # Entities should contain corresponding Schema/DTO/Enum entries
    entities = payload["entities"]
    pet_entities = [e for e in entities if e.get("id") == pet_id]
    assert pet_entities, "Pet schema entity not emitted"
    assert pet_entities[0]["type"] in {"DTO", "Schema", "Enum"}

    # SecurityScheme entity present
    sec = [e for e in entities if e.get("type") == "SecurityScheme" and e.get("name") == "BearerAuth"]
    assert sec, "BearerAuth SecurityScheme entity missing"
    sec_ent = sec[0]
    assert sec_ent.get("scheme_type") == "http"
    assert sec_ent.get("scheme") == "bearer"
    assert sec_ent.get("bearer_format") in {"JWT", "jwt", None}
