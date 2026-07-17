"""Writes parser output to JSON files."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


def write_parser_output(output_dir: Path, results: list[dict[str, Any]]):
    """Write the aggregated parser output to a single JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "openapi_parser_output.json"

    bundle = {
        "version_metadata": {"contract": "parser-json", "version": "1.0"},
        "results": results,
    }

    try:
        with output_file.open("w") as f:
            json.dump(bundle, f, indent=2)
        log.info(f"Successfully wrote parser output to {output_file}")
    except IOError as e:
        log.error(f"Failed to write output to {output_file}: {e}")
