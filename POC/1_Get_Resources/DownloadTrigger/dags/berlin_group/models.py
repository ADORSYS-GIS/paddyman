"""Domain models for the Berlin Group downloader."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DownloadLink:
    """A single downloadable document discovered from a source page."""

    url: str
    filename: str
    version: str
    source_name: str

    def target_path(self, base_dir: Path) -> Path:
        """Compute the local destination path under *base_dir*."""
        safe_version = self.version.replace("/", "-").replace("\\", "-")
        return base_dir / self.source_name / safe_version / self.filename


@dataclass
class DownloadResult:
    """Outcome of a single file-download attempt."""

    link: DownloadLink
    success: bool
    skipped: bool = False
    error: str | None = None
    local_path: str | None = None

    @property
    def status(self) -> str:
        """Human-readable status string."""
        if self.skipped:
            return "skipped"
        return "success" if self.success else "failed"
