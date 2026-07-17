"""Execution reporting helpers for Phase 5."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from typing import Any


@dataclass
class StageRecorder:
    """Collect stage durations, counts, warnings, and errors."""

    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    stages: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def run(self, name: str, action):  # type: ignore[no-untyped-def]
        start = perf_counter()
        try:
            result = action()
            self.add_stage(name, start)
            return result
        except Exception as exc:  # noqa: BLE001
            self.errors.append(f"{name}: {exc}")
            self.add_stage(name, start, error=str(exc))
            raise

    def add_stage(self, name: str, start: float, error: str | None = None) -> None:
        self.stages.append(
            {"name": name, "duration_seconds": round(perf_counter() - start, 4), "error": error}
        )

    def report(self, input_counts: dict[str, int], output_counts: dict[str, int]) -> dict[str, Any]:
        return {
            "execution_timestamp": self.started_at.isoformat(),
            "stages_executed": [stage["name"] for stage in self.stages],
            "stage_durations": self.stages,
            "input_counts": input_counts,
            "output_counts": output_counts,
            "warnings": self.warnings,
            "errors": self.errors,
        }