"""Java discovery package — public API."""
from .build_detector import detect_build_system, find_build_files
from .dependency_detector import extract_maven_metadata
from .gradle_detector import extract_gradle_metadata
from .inventory_builder import build_all_inventories, build_repository_inventory
from .models import (
    BuildSystem,
    GradleMetadata,
    JavaFileRecord,
    MavenMetadata,
    RepositoryInventory,
)
from .module_detector import detect_modules, module_name
from .repository_scanner import (
    count_lines,
    detect_source_root,
    extract_package,
    find_java_files,
)

__all__ = [
    "BuildSystem",
    "MavenMetadata",
    "GradleMetadata",
    "JavaFileRecord",
    "RepositoryInventory",
    "detect_build_system",
    "find_build_files",
    "extract_maven_metadata",
    "extract_gradle_metadata",
    "detect_modules",
    "module_name",
    "find_java_files",
    "extract_package",
    "count_lines",
    "detect_source_root",
    "build_repository_inventory",
    "build_all_inventories",
]
