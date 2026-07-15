"""Canonical parser pipeline runner."""
from __future__ import annotations

import importlib
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

_PARSERS_ROOT = Path(__file__).resolve().parent
_POC_ROOT = _PARSERS_ROOT.parent
for _path in (str(_POC_ROOT), str(_PARSERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from normalized_json import build_normalized_json, write_normalized_json
from shared.config import settings
from shared.models import NormalizedJson

logger = logging.getLogger(__name__)
Runner = Callable[[], Any]
Normalizer = Callable[[dict[str, Any]], NormalizedJson]


@dataclass
class ParserPipelineSummary:
    """Result of one canonical parser pipeline execution."""

    parser_summaries: dict[str, Any] = field(default_factory=dict)
    normalized_output_path: Path | None = None
    documents: int = 0
    entities: int = 0
    relationships: int = 0


def run_pipeline(
    java_runner: Runner | None = None,
    openapi_runner: Runner | None = None,
    markdown_runner: Runner | None = None,
    normalizer: Normalizer | None = None,
    output_path: Path | None = None,
) -> ParserPipelineSummary:
    """Run Java, OpenAPI, and Markdown parsers as one parser pipeline."""
    summaries: dict[str, Any] = {}
    for name, runner in (
        ("java_parser", java_runner or _java_runner),
        ("openapi_parser", openapi_runner or _openapi_runner),
    ):
        logger.info("Running %s", name)
        summaries[name] = runner()

    # Run markdown parser separately, which creates its own output files
    if markdown_runner:
        logger.info("Running markdown_parser")
        summaries["markdown_parser"] = markdown_runner()
    else:
        logger.info("Running markdown_parser")
        summaries["markdown_parser"] = _markdown_runner()

    bundle = (normalizer or build_normalized_json)(summaries)
    path = write_normalized_json(bundle, output_path)
    return ParserPipelineSummary(
        parser_summaries=summaries,
        normalized_output_path=path,
        documents=len(bundle.documents),
        entities=len(bundle.entities),
        relationships=len(bundle.relationships),
    )


def _java_runner() -> Any:
    module = importlib.import_module("java_parser.pipeline")
    return module.run_pipeline(settings.java_parser_source_dir)


def _openapi_runner() -> Any:
    module = importlib.import_module("openapi_parser.main")
    return module.run_pipeline(settings.yaml_spec_dir)


def _markdown_runner() -> Any:
    module = importlib.import_module("markdown_file_output")
    return module.main()


def main() -> None:
    summary = run_pipeline()
    logger.info("Normalized parser output written to %s", summary.normalized_output_path)


if __name__ == "__main__":
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO), format=settings.log_format)
    main()