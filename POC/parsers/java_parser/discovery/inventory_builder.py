"""Inventory builder — composes discovery components into structured output.

Orchestrates repository scanning, build detection, module resolution, and
per-file metadata extraction to produce :class:`~.models.RepositoryInventory`
objects ready for downstream parsing stages.
"""
from __future__ import annotations

import logging
from pathlib import Path

from .build_detector import detect_build_system
from .dependency_detector import extract_maven_metadata
from .gradle_detector import extract_gradle_metadata
from .models import BuildSystem, JavaFileRecord, RepositoryInventory
from .module_detector import detect_modules, module_name
from .repository_scanner import (
    count_lines,
    detect_source_root,
    extract_package,
    find_java_files,
)

logger = logging.getLogger(__name__)


def _build_file_record(
    java_file: Path,
    module_path: Path,
    module_label: str,
    repo_name: str,
    repo_root: Path,
    build_system: BuildSystem,
    project_metadata: dict,
) -> JavaFileRecord:
    """Construct a :class:`JavaFileRecord` for a single ``.java`` file."""
    package = extract_package(java_file)
    lines = count_lines(java_file)
    source_root = detect_source_root(java_file, module_path)

    try:
        relative_path = java_file.relative_to(repo_root).as_posix()
    except ValueError:
        relative_path = java_file.name

    return JavaFileRecord(
        repository=repo_name,
        module=module_label,
        file=java_file.name,
        relative_path=relative_path,
        package=package,
        source_root=source_root,
        lines=lines,
        build_system=build_system.value,
        project_metadata=project_metadata,
    )


def _module_project_metadata(
    module_path: Path, build_system: BuildSystem
) -> dict:
    """Extract lightweight project metadata for a module-level pom/build file."""
    if build_system == BuildSystem.MAVEN:
        pom = module_path / "pom.xml"
        if pom.is_file():
            meta = extract_maven_metadata(pom)
            if meta:
                return {
                    "groupId": meta.group_id,
                    "artifactId": meta.artifact_id,
                    "version": meta.version or "",
                }
    return {}


def build_module_records(
    module_path: Path,
    repo_root: Path,
    repo_name: str,
    build_system: BuildSystem,
) -> list[JavaFileRecord]:
    """Discover and record all Java files within *module_path*.

    Args:
        module_path:  Absolute path to the module root.
        repo_root:    Absolute path to the repository root.
        repo_name:    Human-readable repository name.
        build_system: Build system detected for this repository.

    Returns:
        List of :class:`JavaFileRecord` instances, one per ``.java`` file.
    """
    label = module_name(module_path, repo_root)
    project_meta = _module_project_metadata(module_path, build_system)
    java_files = find_java_files(module_path)
    logger.debug(
        "Module %s/%s: %d Java files found", repo_name, label, len(java_files)
    )

    records: list[JavaFileRecord] = []
    for java_file in java_files:
        try:
            record = _build_file_record(
                java_file=java_file,
                module_path=module_path,
                module_label=label,
                repo_name=repo_name,
                repo_root=repo_root,
                build_system=build_system,
                project_metadata=project_meta,
            )
            records.append(record)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipping %s: %s", java_file, exc)

    return records


def build_repository_inventory(repo_root: Path) -> RepositoryInventory:
    """Produce a complete :class:`RepositoryInventory` for *repo_root*.

    Args:
        repo_root: Absolute path to the repository directory.
    """
    repo_name = repo_root.name
    build_system = detect_build_system(repo_root)
    logger.info("Scanning repository %s (build: %s)", repo_name, build_system.value)

    maven_meta = None
    gradle_meta = None
    errors: list[str] = []

    if build_system == BuildSystem.MAVEN:
        pom = repo_root / "pom.xml"
        if pom.is_file():
            maven_meta = extract_maven_metadata(pom)
            if maven_meta is None:
                errors.append(f"Failed to parse root pom.xml in {repo_name}")
    elif build_system == BuildSystem.GRADLE:
        gradle_meta = extract_gradle_metadata(repo_root)

    module_paths = detect_modules(repo_root)
    module_labels = [module_name(mp, repo_root) for mp in module_paths]

    all_records: list[JavaFileRecord] = []
    for module_path in module_paths:
        records = build_module_records(
            module_path, repo_root, repo_name, build_system
        )
        all_records.extend(records)

    logger.info(
        "Repository %s: %d modules, %d Java files",
        repo_name,
        len(module_paths),
        len(all_records),
    )

    return RepositoryInventory(
        repository=repo_name,
        root_path=repo_root,
        build_system=build_system,
        modules=module_labels,
        files=all_records,
        maven_metadata=maven_meta,
        gradle_metadata=gradle_meta,
        errors=errors,
    )


def build_all_inventories(code_projects_dir: Path) -> list[RepositoryInventory]:
    """Discover and inventory all repositories under *code_projects_dir*.

    Args:
        code_projects_dir: Directory whose immediate sub-directories are
                           treated as individual repositories.

    Returns:
        List of :class:`RepositoryInventory` objects, one per repository.
    """
    if not code_projects_dir.is_dir():
        logger.error("Code projects directory not found: %s", code_projects_dir)
        return []

    inventories: list[RepositoryInventory] = []
    for entry in sorted(code_projects_dir.iterdir()):
        if not entry.is_dir():
            continue
        try:
            inventory = build_repository_inventory(entry)
            inventories.append(inventory)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to inventory repository %s: %s", entry.name, exc)

    return inventories
