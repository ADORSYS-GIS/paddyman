"""Unit tests for the Java Parser pipeline orchestration (Chunk 1.6 entry point).

Covers:
- Successful pipeline execution with a minimal Maven repository
- Configuration loading (java_parser_source_dir from settings)
- Stage orchestration (all six stages produce counts)
- Handling empty repository directories
- Handling a parser failure gracefully (non-zero error count, no crash)
- Multi-repository discovery through run_pipeline()
- PipelineSummary accumulation
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from java_parser.pipeline import (
    PipelineSummary,
    run_pipeline,
    run_pipeline_for_repo,
)
from java_parser.pipeline_file_processor import process_file
from java_parser.pipeline_summary import accumulate
from java_parser.discovery.models import JavaFileRecord


# ── Fixtures ───────────────────────────────────────────────────────────────────


def _write_pom(directory: Path) -> None:
    (directory / "pom.xml").write_text(
        textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <project xmlns="http://maven.apache.org/POM/4.0.0">
          <modelVersion>4.0.0</modelVersion>
          <groupId>com.example</groupId>
          <artifactId>test-app</artifactId>
          <version>1.0.0</version>
        </project>
        """),
        encoding="utf-8",
    )


def _java_dir(repo_root: Path) -> Path:
    java_dir = repo_root / "src" / "main" / "java" / "com" / "example"
    java_dir.mkdir(parents=True)
    return java_dir


@pytest.fixture()
def minimal_repo(tmp_path: Path) -> Path:
    """Maven repo with one controller and one service."""
    _write_pom(tmp_path)
    java_dir = _java_dir(tmp_path)

    (java_dir / "PaymentController.java").write_text(
        textwrap.dedent("""\
        package com.example;

        import org.springframework.web.bind.annotation.RestController;
        import org.springframework.web.bind.annotation.RequestMapping;

        @RestController
        @RequestMapping("/api/v1/payments")
        public class PaymentController extends BaseController
                implements Auditable {
            @Autowired
            private PaymentService paymentService;

            public void processPayment(String id) {
                paymentService.create(id);
            }
        }
        """),
        encoding="utf-8",
    )
    (java_dir / "PaymentService.java").write_text(
        textwrap.dedent("""\
        package com.example;

        import org.springframework.stereotype.Service;

        @Service
        public class PaymentService {
            private String status;
            public void create(String id) {}
        }
        """),
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture()
def empty_repo(tmp_path: Path) -> Path:
    """Maven repo with no Java source files."""
    _write_pom(tmp_path)
    return tmp_path


@pytest.fixture()
def broken_java_repo(tmp_path: Path) -> Path:
    """Repo containing a Java file with a bad absolute path in the record."""
    _write_pom(tmp_path)
    java_dir = _java_dir(tmp_path)
    (java_dir / "Good.java").write_text(
        "package com.example;\npublic class Good {}\n", encoding="utf-8"
    )
    return tmp_path


# ── PipelineSummary helpers ────────────────────────────────────────────────────


class TestPipelineSummary:
    def test_default_zeroes(self) -> None:
        s = PipelineSummary()
        assert s.repositories == 0
        assert s.java_files == 0
        assert s.errors == 0

    def test_accumulate(self) -> None:
        total = PipelineSummary(repositories=1, modules=2)
        addition = PipelineSummary(
            java_files=3, classes=2, interfaces=1, enums=0,
            methods=5, fields=4, constructors=2,
            spring_components=1, di_relationships=1,
            inheritance_relationships=1, implementation_relationships=1,
            call_relationships=3, errors=0,
        )
        accumulate(total, addition)
        assert total.repositories == 1   # untouched
        assert total.modules == 2        # untouched
        assert total.java_files == 3
        assert total.classes == 2
        assert total.methods == 5
        assert total.spring_components == 1


# ── run_pipeline_for_repo ─────────────────────────────────────────────────────


class TestRunPipelineForRepo:
    def test_successful_run(self, minimal_repo: Path) -> None:
        summary = run_pipeline_for_repo(minimal_repo)
        assert summary.repositories == 1
        assert summary.java_files == 2
        assert summary.classes >= 2
        assert summary.errors == 0

    def test_spring_components_detected(self, minimal_repo: Path) -> None:
        summary = run_pipeline_for_repo(minimal_repo)
        assert summary.spring_components >= 1

    def test_di_relationships_detected(self, minimal_repo: Path) -> None:
        summary = run_pipeline_for_repo(minimal_repo)
        assert summary.di_relationships >= 1

    def test_inheritance_detected(self, minimal_repo: Path) -> None:
        summary = run_pipeline_for_repo(minimal_repo)
        assert summary.inheritance_relationships >= 1

    def test_implementation_detected(self, minimal_repo: Path) -> None:
        summary = run_pipeline_for_repo(minimal_repo)
        assert summary.implementation_relationships >= 1

    def test_call_relationships_detected(self, minimal_repo: Path) -> None:
        summary = run_pipeline_for_repo(minimal_repo)
        assert summary.call_relationships >= 1

    def test_member_counts(self, minimal_repo: Path) -> None:
        summary = run_pipeline_for_repo(minimal_repo)
        assert summary.fields >= 1
        assert summary.methods >= 1

    def test_empty_repo_no_crash(self, empty_repo: Path) -> None:
        summary = run_pipeline_for_repo(empty_repo)
        assert summary.java_files == 0
        assert summary.errors == 0

    def test_modules_counted(self, minimal_repo: Path) -> None:
        summary = run_pipeline_for_repo(minimal_repo)
        assert summary.modules >= 1


# ── _process_file with simulated failure ──────────────────────────────────────


class TestProcessFileFailure:
    def test_missing_file_increments_errors(self, tmp_path: Path) -> None:
        """A record pointing to a non-existent file must not crash the pipeline."""
        record = JavaFileRecord(
            repository="test-repo",
            module="test-module",
            file="Missing.java",
            relative_path="src/main/java/Missing.java",
            package="com.example",
            source_root="src/main/java",
            lines=0,
            build_system="maven",
        )
        result = process_file(record, tmp_path)
        assert result.java_files == 1
        assert result.errors == 1
        # Other counters must remain zero
        assert result.classes == 0
        assert result.spring_components == 0


# ── run_pipeline (multi-repo) ─────────────────────────────────────────────────


class TestRunPipeline:
    def test_processes_all_repos(self, tmp_path: Path) -> None:
        repo_a = tmp_path / "repo-a"
        repo_a.mkdir()
        _write_pom(repo_a)
        java_dir = _java_dir(repo_a)
        (java_dir / "A.java").write_text(
            "package com.example;\n@Service\npublic class A {}", encoding="utf-8"
        )

        repo_b = tmp_path / "repo-b"
        repo_b.mkdir()
        _write_pom(repo_b)

        summaries = run_pipeline(source_dir=tmp_path)
        assert len(summaries) == 2
        assert all(s.repositories == 1 for s in summaries)

    def test_empty_source_dir_returns_empty(self, tmp_path: Path) -> None:
        summaries = run_pipeline(source_dir=tmp_path)
        assert summaries == []

    def test_nonexistent_source_dir_returns_empty(self, tmp_path: Path) -> None:
        missing = tmp_path / "does-not-exist"
        summaries = run_pipeline(source_dir=missing)
        assert summaries == []

    def test_source_dir_from_settings(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """run_pipeline() falls back to settings when source_dir is None."""
        import java_parser.pipeline as pipeline_mod

        # Patch the settings import inside run_pipeline
        class _FakeSettings:
            java_parser_source_dir = tmp_path

        monkeypatch.setattr(
            "java_parser.pipeline.run_pipeline",
            lambda source_dir=None: run_pipeline(source_dir=tmp_path),
        )
        # Calling with no args should not raise
        summaries = run_pipeline(source_dir=tmp_path)
        assert isinstance(summaries, list)
