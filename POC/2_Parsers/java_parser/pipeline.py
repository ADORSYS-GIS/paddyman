"""Java Parser pipeline orchestration.

Runs all implemented pipeline stages in order for one or more repositories:

1. Repository discovery      (java_parser.discovery)
2. Resource file discovery   (java_parser.resources)
3. Java AST parsing          (java_parser.java_ast)
4. Member extraction         (java_parser.members)
5. Spring annotation extractor (java_parser.spring)
6. Dependency injection extractor (java_parser.di)
7. Relationship extractor    (java_parser.relationships)
8. Resource file parsing     (java_parser.resources)

Consumers of this module should call :func:`run_pipeline` (multi-repo) or
:func:`run_pipeline_for_repo` (single repo).  The entry point :mod:`main`
calls :func:`run_pipeline` using the path from shared configuration.
"""
from __future__ import annotations

import logging
from pathlib import Path

from java_parser.discovery.inventory_builder import build_repository_inventory
from java_parser.discovery.module_detector import detect_modules
from java_parser.pipeline_file_processor import process_file
from java_parser.pipeline_summary import PipelineSummary, accumulate
from java_parser.resources import scan_and_parse_resources

logger = logging.getLogger(__name__)


def run_pipeline_for_repo(repo_root: Path) -> PipelineSummary:
    """Execute the complete pipeline for a single repository.

    Args:
        repo_root: Absolute path to the repository directory.

    Returns:
        :class:`PipelineSummary` with aggregated counts.
    """
    logger.info("Pipeline starting for repository: %s", repo_root.name)
    inventory = build_repository_inventory(repo_root)
    summary = PipelineSummary(
        repositories=1,
        modules=len(inventory.modules),
    )

    # Stage 2 + 8 — resource file discovery and parsing
    module_paths = detect_modules(repo_root)
    res = scan_and_parse_resources(repo_root, module_paths)
    summary.resource_files = res.total_files
    summary.properties_files = res.properties_count
    summary.yaml_files = res.yaml_count
    summary.xml_files = res.xml_count
    summary.pom_files = res.pom_count
    summary.migration_files = res.migration_count
    summary.config_keys = res.config_keys
    summary.maven_dependencies = res.maven_deps
    summary.errors += res.errors

    # Stages 3–7 — Java file processing
    for record in inventory.files:
        accumulate(summary, process_file(record, repo_root))

    logger.info(
        "Repository %s: %d java files, %d resource files, %d classes, %d errors",
        repo_root.name,
        summary.java_files,
        summary.resource_files,
        summary.classes,
        summary.errors,
    )
    return summary


def run_pipeline(source_dir: Path | None = None) -> list[PipelineSummary]:
    """Execute the pipeline for every repository under *source_dir*.

    When *source_dir* is ``None`` the path is obtained from
    :data:`shared.config.settings` (``settings.java_parser_source_dir``).

    Args:
        source_dir: Directory whose immediate children are Java repositories.
                    Skips entries that are not directories.

    Returns:
        One :class:`PipelineSummary` per processed repository.
    """
    if source_dir is None:
        from shared.config import settings  # deferred to avoid import-time side effects

        source_dir = settings.java_parser_source_dir

    if not source_dir.exists():
        logger.error("Source directory does not exist: %s", source_dir)
        return []

    repo_dirs = sorted(p for p in source_dir.iterdir() if p.is_dir())
    if not repo_dirs:
        logger.warning("No repository directories found under %s", source_dir)
        return []

    summaries: list[PipelineSummary] = []
    for repo_dir in repo_dirs:
        try:
            summaries.append(run_pipeline_for_repo(repo_dir))
        except Exception as exc:  # noqa: BLE001
            logger.error("Pipeline failed for repository %s: %s", repo_dir.name, exc)

    return summaries
