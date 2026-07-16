"""Java Parser pipeline entry point.

Executes the complete Java parser pipeline against the configured source
repository directory and prints a structured summary to the console.

Usage (from POC/2_Parsers/java_parser/)::

    python main.py

Or from the POC root::

    python -m java_parser.main

The source directory is read from ``settings.java_parser_source_dir``
(environment variable ``JAVA_PARSER_SOURCE_DIR``; default:
``POC/DataSource/code_projects``).
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure POC/ (for shared.*) and POC/2_Parsers/ (for java_parser.*) are on the
# path regardless of the working directory the script is invoked from.
_here = Path(__file__).resolve().parent          # POC/2_Parsers/java_parser/
_parsers_dir = _here.parent                      # POC/2_Parsers/
_poc_dir = _parsers_dir.parent                   # POC/
for _p in (_poc_dir, _parsers_dir):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from shared.config import settings  # noqa: E402

from java_module_output import write_java_module_normalized_jsons  # noqa: E402
from java_parser.pipeline import PipelineSummary, run_pipeline

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format=settings.log_format,
        stream=sys.stdout,
    )


def _print_summary(summaries: list[PipelineSummary]) -> None:
    """Log a structured summary of the pipeline run."""
    if not summaries:
        logger.info("No repositories processed.")
        return

    total = PipelineSummary()
    for s in summaries:
        total.repositories += s.repositories
        total.modules += s.modules
        total.java_files += s.java_files
        total.classes += s.classes
        total.interfaces += s.interfaces
        total.enums += s.enums
        total.methods += s.methods
        total.fields += s.fields
        total.constructors += s.constructors
        total.spring_components += s.spring_components
        total.di_relationships += s.di_relationships
        total.inheritance_relationships += s.inheritance_relationships
        total.implementation_relationships += s.implementation_relationships
        total.call_relationships += s.call_relationships
        total.errors += s.errors
        total.resource_files += s.resource_files
        total.properties_files += s.properties_files
        total.yaml_files += s.yaml_files
        total.xml_files += s.xml_files
        total.pom_files += s.pom_files
        total.migration_files += s.migration_files
        total.config_keys += s.config_keys
        total.maven_dependencies += s.maven_dependencies

    logger.info("=" * 60)
    logger.info("Java Parser Pipeline — Summary")
    logger.info("=" * 60)
    logger.info("Repositories scanned:          %6d", total.repositories)
    logger.info("Modules discovered:            %6d", total.modules)
    logger.info("Java files processed:          %6d", total.java_files)
    logger.info("  Classes:                     %6d", total.classes)
    logger.info("  Interfaces:                  %6d", total.interfaces)
    logger.info("  Enums:                       %6d", total.enums)
    logger.info("  Methods extracted:           %6d", total.methods)
    logger.info("  Fields extracted:            %6d", total.fields)
    logger.info("  Constructors extracted:      %6d", total.constructors)
    logger.info("Spring components found:       %6d", total.spring_components)
    logger.info("DI relationships:              %6d", total.di_relationships)
    logger.info("Inheritance relationships:     %6d", total.inheritance_relationships)
    logger.info("Implementation relationships:  %6d", total.implementation_relationships)
    logger.info("Method call relationships:     %6d", total.call_relationships)
    logger.info("Errors (non-fatal):            %6d", total.errors)
    logger.info("-" * 60)
    logger.info("Resource files discovered:     %6d", total.resource_files)
    logger.info("  Properties files:            %6d", total.properties_files)
    logger.info("  YAML files:                  %6d", total.yaml_files)
    logger.info("  XML files:                   %6d", total.xml_files)
    logger.info("    POM files:                 %6d", total.pom_files)
    logger.info("    Migration files:           %6d", total.migration_files)
    logger.info("Config keys extracted:         %6d", total.config_keys)
    logger.info("Maven dependencies found:      %6d", total.maven_dependencies)
    logger.info("=" * 60)


def main() -> None:
    _configure_logging()
    source_dir = settings.java_parser_source_dir
    if not source_dir.is_absolute():
        source_dir = (_poc_dir / source_dir).resolve()
    logger.info("Java Parser pipeline starting — source: %s", source_dir)
    summaries = run_pipeline(source_dir)
    output_paths = write_java_module_normalized_jsons({"java_parser": [s.__dict__ for s in summaries]}, source_dir)
    logger.info("Java parser module outputs written to %s (%d files)", settings.parser_output_dir / "java_code", len(output_paths))
    _print_summary(summaries)


if __name__ == "__main__":
    main()
