"""Unit tests for shared.models.context."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

import pytest

from shared.models.context import PipelineContext


class TestPipelineContextCreation:
    def test_minimal_required_fields(self) -> None:
        ctx = PipelineContext(pipeline_id="extraction-pipeline")
        assert ctx.pipeline_id == "extraction-pipeline"
        assert isinstance(ctx.id, UUID)
        assert isinstance(ctx.trace_id, str)
        assert isinstance(ctx.started_at, datetime)
        assert ctx.config == {}
        assert ctx.metadata == {}

    def test_each_instance_gets_unique_id(self) -> None:
        a = PipelineContext(pipeline_id="p")
        b = PipelineContext(pipeline_id="p")
        assert a.id != b.id

    def test_each_instance_gets_unique_trace_id(self) -> None:
        a = PipelineContext(pipeline_id="p")
        b = PipelineContext(pipeline_id="p")
        assert a.trace_id != b.trace_id

    def test_config_stored(self) -> None:
        cfg = {"batch_size": 50, "max_retries": 3}
        ctx = PipelineContext(pipeline_id="p", config=cfg)
        assert ctx.config == cfg

    def test_metadata_stored(self) -> None:
        ctx = PipelineContext(pipeline_id="p", metadata={"stage": "extraction"})
        assert ctx.metadata["stage"] == "extraction"

    def test_started_at_is_utc_aware(self) -> None:
        ctx = PipelineContext(pipeline_id="p")
        assert ctx.started_at.tzinfo is not None


class TestPipelineContextValidation:
    def test_empty_pipeline_id_raises(self) -> None:
        with pytest.raises(ValueError, match="pipeline_id"):
            PipelineContext(pipeline_id="")

    def test_whitespace_pipeline_id_raises(self) -> None:
        with pytest.raises(ValueError, match="pipeline_id"):
            PipelineContext(pipeline_id="   ")


class TestPipelineContextIsolation:
    def test_mutable_fields_are_independent_across_instances(self) -> None:
        a = PipelineContext(pipeline_id="p")
        b = PipelineContext(pipeline_id="p")
        a.metadata["key"] = "value"
        assert "key" not in b.metadata
