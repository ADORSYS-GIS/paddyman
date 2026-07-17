"""Integration test: SecurityScheme entities and operation relationships.

Ensures that security schemes defined under `components.securitySchemes`
are emitted as `SecurityScheme` entities and that `Operation` entities
are linked to them via `REQUIRES_SECURITY` relationships.
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


def test_security_scheme_emitted_and_operation_linked(tmp_path: Path) -> None:
    payload = _render_payload(
        tmp_path,
        """openapi: 3.0.1
info:
  title: Test API
  version: 1.0.0
components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
paths:
  /items:
    get:
      operationId: listItems
      security:
        - ApiKeyAuth: []
      responses:
        '200':
          description: OK
""",
    )

    entities = payload.get("entities") or []
    relationships = payload.get("relationships") or []

    # Security scheme entity exists
    sec = [e for e in entities if e.get("type") == "SecurityScheme" and e.get("name") == "ApiKeyAuth"]
    assert sec, "ApiKeyAuth SecurityScheme entity missing"
    sec_ent = sec[0]
    assert sec_ent.get("scheme_type") in {"apiKey", "apikey"}
    assert sec_ent.get("source_location") == "#/components/securitySchemes/ApiKeyAuth"

    # Operation entity present
    ops = [e for e in entities if e.get("type") == "Operation"]
    op = None
    for o in ops:
        props = o.get("properties") or {}
        if props.get("operation_id") == "listItems":
            op = o
            break
    assert op is not None, "Operation 'listItems' not emitted"

    # Relationship linking operation -> security scheme exists
    reqs = [r for r in relationships if r.get("type") == "REQUIRES_SECURITY"]
    assert any(
        r.get("properties", {}).get("operation_id") == "listItems" and r.get("properties", {}).get("security_scheme") == "ApiKeyAuth"
        for r in reqs
    ), "REQUIRES_SECURITY relationship for operation 'listItems' -> ApiKeyAuth missing"
