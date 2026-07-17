"""OpenAPI Parser pipeline orchestrator."""
from __future__ import annotations

import logging
import sys
from pathlib import Path


def _setup_paths():
    """Add POC directory and parsers directory to sys.path for imports."""
    script = Path(__file__).resolve()
    poc_root = script.parents[2]  # POC/
    parsers_dir = script.parents[1]  # POC/parsers/
    for p in (str(poc_root), str(parsers_dir)):
        if p not in sys.path:
            sys.path.insert(0, p)


_setup_paths()

from shared.config import settings
from openapi_parser.file_finder import find_openapi_specs
from openapi_parser.spec_processor import process_spec
from openapi_parser.summary import log_summary
import json

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s — %(message)s")
log = logging.getLogger(__name__)


def main():
    """Main function to run the OpenAPI parser pipeline."""

    source_dir = settings.yaml_spec_dir
    output_dir = settings.parser_output_dir / "openapi"

    spec_files = find_openapi_specs(source_dir)
    results = [result for spec in spec_files if (result := process_spec(spec))]

    if results:
        # Write one JSON file per source spec into the parser output directory.
        target_dir = output_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        # remove existing JSON files to avoid stale outputs
        for old in target_dir.glob("*.json"):
            try:
                old.unlink()
            except Exception:
                pass

        spec_root = Path(settings.yaml_spec_dir)

        def _safe_spec_name(root: Path, path_str: str) -> str:
            try:
                p = Path(path_str)
                rel = p.relative_to(root).with_suffix("").as_posix()
            except Exception:
                rel = Path(path_str).stem
            return "".join(c if c.isalnum() or c in {"-", "_"} else "_" for c in rel)

        for spec in results:
            source = spec.get("source_file") or "unknown"
            name = _safe_spec_name(spec_root, source)
            out_path = target_dir / f"{name}.json"
            try:
                # Write only the API object as the top-level JSON payload.
                out_obj = spec.get("api") or spec
                with out_path.open("w") as f:
                    json.dump(out_obj, f, indent=2)
            except Exception:
                log.exception("Failed to write spec output to %s", out_path)

        log_summary(results)
    else:
        log.warning("No OpenAPI specifications were successfully processed.")


if __name__ == "__main__":
    main()

