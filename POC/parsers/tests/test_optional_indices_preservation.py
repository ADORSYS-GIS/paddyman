import json
import sys
from pathlib import Path

# Ensure POC/ and POC/2_Parsers/ are on the import path for tests
_POC_ROOT = Path(__file__).resolve().parents[2]
_PARSERS_ROOT = _POC_ROOT / "2_Parsers"
for _p in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from shared.models import NormalizedJson
from normalized_json import build_normalized_json


def test_parser_indices_preserved_from_parser_outputs(tmp_path):
    # Create a fake parser output directory with one module JSON
    out = tmp_path / "parser_outputs"
    out.mkdir()
    file_path = out / "repo_module.json"
    payload = {
        "documents": [],
        "entities": [],
        "relationships": [],
        "version_metadata": {"contract": "parser-json", "version": "1.0"},
        "parser_indices": {"method_calls": [{"id": "m1"}]},
    }
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    bundle = build_normalized_json(None, parser_output_dir=out)
    d = bundle.to_dict()
    assert "parser_indices" in d
    assert "method_calls" in d["parser_indices"]
    # Aggregator namespaces by source filename
    assert "repo_module.json" in d["parser_indices"]["method_calls"]
    assert d["parser_indices"]["method_calls"]["repo_module.json"][0]["id"] == "m1"
