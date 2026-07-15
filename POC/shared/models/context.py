"""Domain model for shared pipeline execution context.

PipelineContext carries the identity and configuration of a pipeline run.
It is passed between stages to provide a stable reference point for logging,
tracing, and per-run configuration — without becoming a catch-all for
arbitrary runtime state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass
class PipelineContext:
    """Shared execution context passed between pipeline stages.

    Args:
        pipeline_id: Human-readable name or identifier for the pipeline.
        id:          Unique run identifier; auto-generated when omitted.
        trace_id:    Correlation ID for distributed tracing; auto-generated when omitted.
        started_at:  UTC timestamp when the pipeline run began; defaults to now.
        config:      Immutable pipeline configuration values for this run.
        metadata:    Runtime annotations added by pipeline stages.
    """

    pipeline_id: str
    id: UUID = field(default_factory=uuid4)
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    started_at: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.pipeline_id.strip():
            raise ValueError("PipelineContext.pipeline_id must not be empty")
