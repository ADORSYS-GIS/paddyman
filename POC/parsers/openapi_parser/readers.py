"""LlamaIndex-based document readers for OpenAPI specifications (Chunk 3.2).

Provides two reader functions:

* :func:`read_local` — loads YAML files from a local directory using
  LlamaIndex ``SimpleDirectoryReader``.
* :func:`read_gitlab` — loads YAML files from a GitLab repository using
  LlamaIndex ``GitLabRepositoryReader``.

Both functions return a list of LlamaIndex ``Document`` objects whose text
is raw YAML content.  :func:`endpoints_from_documents` converts that list
into :class:`~openapi_parser.models.EndpointMetadata` records.

GitLab access is fully isolated in :func:`read_gitlab`; the rest of the
module performs no network I/O.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from gitlab import Gitlab
from llama_index.core import SimpleDirectoryReader
from llama_index.readers.gitlab import GitLabRepositoryReader

from openapi_parser.extractor import extract_endpoints
from openapi_parser.info_extractor import (
    InfoExtractionError,
    extract_info_metadata,
)
from openapi_parser.models import EndpointMetadata, OpenApiMetadata

logger = logging.getLogger(__name__)

_YAML_SUFFIXES: frozenset[str] = frozenset({".yaml", ".yml"})


def read_local(source_dir: Path | str | None = None) -> list[Any]:
    """Load OpenAPI YAML files from *source_dir* using ``SimpleDirectoryReader``.

    When *source_dir* is ``None`` the path is read from
    :data:`shared.config.settings.yaml_spec_dir`.

    Args:
        source_dir: Root directory to scan recursively for YAML files.

    Returns:
        List of LlamaIndex ``Document`` objects whose ``text`` is YAML content.
    """
    from shared.config import settings  # deferred for testability

    resolved = (
        Path(source_dir) if source_dir is not None else Path(settings.yaml_spec_dir)
    )

    if not resolved.exists() or not resolved.is_dir():
        logger.warning(
            "YAML spec directory does not exist or is not a directory: %s", resolved
        )
        return []

    try:
        reader = SimpleDirectoryReader(
            str(resolved),
            recursive=True,
            required_exts=sorted(_YAML_SUFFIXES),
        )
        docs = reader.load_data()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load documents from %s: %s", resolved, exc)
        return []

    logger.info("SimpleDirectoryReader loaded %d document(s) from %s", len(docs), resolved)
    return list(docs) if docs else []


def read_gitlab(
    project_id: int,
    ref: str = "main",
    path: str | None = None,
    use_adorsys: bool = False,
) -> list[Any]:
    """Load OpenAPI YAML files from a GitLab repository.

    Configuration is read from :data:`shared.config.settings`:

    * ``gitlab_base_url`` / ``gitlab_token`` — public GitLab.
    * ``adorsys_base_url`` / ``adorsys_token`` — Adorsys GitLab instance.

    Args:
        project_id:   GitLab numeric project identifier.
        ref:          Branch name or commit SHA to read from.
        path:         Optional subdirectory within the repository.
        use_adorsys:  When ``True`` uses the Adorsys GitLab instance.

    Returns:
        List of LlamaIndex ``Document`` objects filtered to YAML files only.
    """
    from shared.config import settings  # deferred for testability

    base_url = settings.adorsys_base_url if use_adorsys else settings.gitlab_base_url
    token = settings.adorsys_token if use_adorsys else settings.gitlab_token

    gl = Gitlab(url=base_url, private_token=token)

    try:
        reader = GitLabRepositoryReader(gitlab_client=gl, project_id=project_id)
        all_docs = reader.load_data(ref=ref, path=path, recursive=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "GitLabRepositoryReader failed for project %s@%s: %s", project_id, ref, exc
        )
        return []

    yaml_docs = [
        d for d in all_docs
        if Path(d.metadata.get("file_path", "")).suffix.lower() in _YAML_SUFFIXES
    ]
    logger.info(
        "GitLabRepositoryReader loaded %d YAML document(s) from project %s",
        len(yaml_docs),
        project_id,
    )
    return yaml_docs


def endpoints_from_documents(docs: list[Any]) -> list[EndpointMetadata]:
    """Convert LlamaIndex Documents into :class:`~openapi_parser.models.EndpointMetadata`.

    Each Document's text is treated as YAML content.  Documents that cannot
    be parsed or that lack required OpenAPI fields are skipped with a warning.

    Args:
        docs: List of LlamaIndex Document objects.

    Returns:
        Flat list of all endpoints extracted across all documents.
    """
    results: list[EndpointMetadata] = []
    for doc in docs:
        text = doc.text
        if isinstance(text, bytes):
            text = text.decode("utf-8", errors="replace")

        spec_source: str = doc.metadata.get("file_path") or doc.id_ or "<unknown>"

        try:
            raw: Any = yaml.load(text, Loader=yaml.CSafeLoader)
        except yaml.YAMLError as exc:
            logger.warning("Skipping document %s — invalid YAML: %s", spec_source, exc)
            continue

        if not isinstance(raw, dict):
            logger.warning("Skipping %s — YAML root is not a mapping.", spec_source)
            continue

        try:
            metadata_dict = extract_info_metadata(raw, spec_source)
            meta = OpenApiMetadata(spec_file=spec_source, **metadata_dict)
        except InfoExtractionError as exc:
            logger.warning("Skipping %s — %s", spec_source, exc)
            continue

        endpoints = extract_endpoints(raw, api_title=meta.title, spec_source=spec_source)
        results.extend(endpoints)

    logger.info("Extracted %d endpoint(s) from %d document(s)", len(results), len(docs))
    return results
