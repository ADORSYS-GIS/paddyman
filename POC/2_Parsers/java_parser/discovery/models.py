"""Domain models for the Java discovery phase.

These models carry the structured inventory produced by scanning Java
repositories.  They are intentionally separate from the shared pipeline models
to keep parser-specific schema evolution independent.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class BuildSystem(str, Enum):
    """Detected build system for a Java project."""

    MAVEN = "maven"
    GRADLE = "gradle"
    UNKNOWN = "unknown"


@dataclass
class MavenMetadata:
    """Metadata extracted from a Maven pom.xml.

    Args:
        group_id:             Maven groupId.
        artifact_id:          Maven artifactId.
        version:              Project version (may be None for child modules
                              that inherit the version).
        parent_group_id:      Parent groupId when a ``<parent>`` is declared.
        parent_artifact_id:   Parent artifactId when a ``<parent>`` is declared.
        parent_version:       Parent version when a ``<parent>`` is declared.
        declared_modules:     Sub-module names listed in ``<modules>``.
        dependencies:         List of ``{groupId, artifactId, version}`` dicts.
    """

    group_id: str
    artifact_id: str
    version: str | None = None
    parent_group_id: str | None = None
    parent_artifact_id: str | None = None
    parent_version: str | None = None
    declared_modules: list[str] = field(default_factory=list)
    dependencies: list[dict[str, str]] = field(default_factory=list)


@dataclass
class GradleMetadata:
    """Metadata extracted from a Gradle build / settings file.

    Args:
        project_name:         Value of ``rootProject.name`` in settings file.
        included_builds:      Paths declared via ``includeBuild()``.
        project_dependencies: Project paths declared via ``project(':...')``.
    """

    project_name: str | None = None
    included_builds: list[str] = field(default_factory=list)
    project_dependencies: list[str] = field(default_factory=list)


@dataclass
class JavaFileRecord:
    """Inventory record for a single Java source file.

    Args:
        repository:       Name of the owning repository.
        module:           Name of the Maven / Gradle module (or repository name
                          when the repo is not multi-module).
        file:             Bare filename (e.g. ``UserController.java``).
        relative_path:    Path relative to the repository root.
        package:          Java package declared in the file, or empty string.
        source_root:      Source root directory relative to the module root
                          (e.g. ``src/main/java``).
        lines:            Total line count of the file.
        build_system:     Detected build system label.
        project_metadata: Arbitrary parser-stage annotations.
    """

    repository: str
    module: str
    file: str
    relative_path: str
    package: str
    source_root: str
    lines: int
    build_system: str
    project_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary (suitable for JSON output)."""
        return {
            "repository": self.repository,
            "module": self.module,
            "file": self.file,
            "relative_path": self.relative_path,
            "package": self.package,
            "source_root": self.source_root,
            "lines": self.lines,
            "build_system": self.build_system,
            "project_metadata": self.project_metadata,
        }


@dataclass
class RepositoryInventory:
    """Aggregated discovery inventory for one repository.

    Args:
        repository:       Repository directory name.
        root_path:        Absolute path to the repository root.
        build_system:     Primary build system detected at the root.
        modules:          Discovered module names.
        files:            All discovered Java file records.
        maven_metadata:   Root-level Maven metadata (when applicable).
        gradle_metadata:  Root-level Gradle metadata (when applicable).
        errors:           Non-fatal error messages collected during discovery.
    """

    repository: str
    root_path: Path
    build_system: BuildSystem
    modules: list[str] = field(default_factory=list)
    files: list[JavaFileRecord] = field(default_factory=list)
    maven_metadata: MavenMetadata | None = None
    gradle_metadata: GradleMetadata | None = None
    errors: list[str] = field(default_factory=list)
