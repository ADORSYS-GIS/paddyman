"""Resource file discovery for Spring Boot repositories.

Scans a repository directory for ``.properties``, ``.yml``, ``.yaml``, and
``.xml`` files, skipping generated/build output directories.
"""
from __future__ import annotations

import logging
from pathlib import Path

from .models import ResourceFile, ResourceFileType

logger = logging.getLogger(__name__)

_EXCLUDED_DIRS: frozenset[str] = frozenset(
    {".git", "target", "build", ".gradle", "node_modules", ".mvn", ".idea"}
)

_EXTENSION_TYPE: dict[str, ResourceFileType] = {
    ".properties": ResourceFileType.PROPERTIES,
    ".yml": ResourceFileType.YAML,
    ".yaml": ResourceFileType.YAML,
    ".xml": ResourceFileType.XML,
}


def _is_excluded(path: Path, repo_root: Path) -> bool:
    """Return ``True`` when any path component is an excluded directory."""
    try:
        relative = path.relative_to(repo_root)
    except ValueError:
        return False
    return any(part in _EXCLUDED_DIRS for part in relative.parts)


def _assign_module(abs_path: Path, module_paths: list[Path], repo_root: Path) -> str:
    """Return the most-specific module name that contains *abs_path*.

    Picks the module with the longest path prefix (deepest match).  Falls back
    to ``"root"`` when no module path is an ancestor.

    Args:
        abs_path:     Absolute path to the resource file.
        module_paths: Absolute module root directories (from ``detect_modules``).
        repo_root:    Repository root used to build a relative label.
    """
    best: Path | None = None
    for mp in module_paths:
        try:
            abs_path.relative_to(mp)
        except ValueError:
            continue
        if best is None or len(mp.parts) > len(best.parts):
            best = mp
    if best is None:
        return "root"
    try:
        return best.relative_to(repo_root).as_posix()
    except ValueError:
        return best.name


def find_resource_files(
    repo_root: Path,
    module_paths: list[Path],
    *,
    repository: str = "",
) -> list[ResourceFile]:
    """Walk *repo_root* and collect all recognised resource files.

    Excludes paths under build-output directories (``target/``, ``build/``,
    ``.gradle/``, etc.) and hidden VCS directories.

    Args:
        repo_root:    Absolute path to the repository root.
        module_paths: Absolute module root directories for label assignment.
        repository:   Repository label embedded in every record; defaults to
                      ``repo_root.name``.

    Returns:
        Sorted list of :class:`ResourceFile` instances.
    """
    repo_name = repository or repo_root.name
    records: list[ResourceFile] = []

    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _EXTENSION_TYPE:
            continue
        if _is_excluded(path, repo_root):
            continue

        rel_path = path.relative_to(repo_root)
        file_type = _EXTENSION_TYPE[path.suffix.lower()]
        module_label = _assign_module(path, module_paths, repo_root)

        records.append(
            ResourceFile(
                repository=repo_name,
                module=module_label,
                file=path.name,
                relative_path=str(rel_path),
                file_type=file_type.value,
            )
        )

    logger.debug("Found %d resource files in %s", len(records), repo_name)
    return records
