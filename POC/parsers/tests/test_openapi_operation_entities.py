import json
from pathlib import Path
from uuid import UUID
from shared.models.openapi import Operation, Endpoint, Tag


from parsers.openapi_parser.models import EndpointMetadata
import json
from pathlib import Path
from uuid import UUID
from shared.models.openapi import Operation, Endpoint, Tag


def _render_payload(tmp_path: Path, spec_content: str) -> dict:
    """Helper to run the parser and return the JSON output."""
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_path = spec_dir / "payment.yaml"
    spec_path.write_text(spec_content, encoding="utf-8")

    # This is a simplified mock of the real pipeline
    from parsers.openapi_parser.operation_extractor import extract_operation_entities
    from parsers.openapi_parser.endpoint_entity_builder import build_endpoint_entity

    raw_spec = {"info": {"title": "Payment API"}, "paths": {"/payments": {"post": {"operationId": "createPayment", "tags": ["payments", "pis"]}}}}

    endpoint_meta = EndpointMetadata(
        type="endpoint",
        path="/payments",
        method="post",
        spec_source=str(spec_path),
        api_title="Payment API",
        parameters=[],
    )
    endpoint = build_endpoint_entity(endpoint_meta)
    operations, tags, _ = extract_operation_entities(raw_spec, str(spec_path))

    entities = [endpoint.dict(), *(op.dict() for op in operations), *(tag.dict() for tag in tags)]

    return {"entities": entities}



def test_creates_operation_and_tag_entities(tmp_path: Path):
    payload = _render_payload(
        tmp_path,
        """
        openapi: 3.0.1
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

    assert endpoint["name"] == "POST /payments"
    assert operation["name"] == "createPayment"
    assert operation["endpoint_id"] == endpoint["id"]
    assert {t["name"] for t in tags} == {"payments", "pis"}


def test_operation_has_correct_endpoint_id(tmp_path: Path):
    payload = _render_payload(
        tmp_path,
        """
        openapi: 3.0.1
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
    endpoint = Endpoint(**next(e for e in entities if e["type"] == "Endpoint"))
    operation = Operation(**next(o for o in entities if o["type"] == "Operation"))

    assert isinstance(endpoint, Endpoint)
    assert isinstance(operation, Operation)
    assert operation.endpoint_id == endpoint.id

