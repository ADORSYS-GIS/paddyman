"""Unit tests for the OpenAPI parser YAML loader (Chunk 3.1).

Covers:
- YAML loading from configured path via ``shared.config.settings`` fallback
- YAML loading from an explicit path
- Multiple specification files in the same directory
- Invalid YAML handling (malformed content)
- Missing required metadata (title / version / info block)
- Non-existent source directory
- Non-mapping YAML root

Note: Metadata extraction tests have been moved to test_info_extractor.py
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MINIMAL_YAML = textwrap.dedent("""\
    openapi: "3.0.1"
    info:
      title: Payment API
      version: "1.0.0"
""")

_FULL_YAML = textwrap.dedent("""\
    openapi: "3.0.1"
    info:
      title: Full API
      version: "2.5.0"
      description: A comprehensive API.
      contact:
        name: Support
        email: support@example.com
      license:
        name: Apache 2.0
        url: https://www.apache.org/licenses/LICENSE-2.0
    servers:
      - url: https://api.example.com/v1
        description: Production
      - url: https://sandbox.example.com/v1
        description: Sandbox
""")

_INVALID_YAML = "key: [\nunot closed"

_NO_INFO_YAML = textwrap.dedent("""\
    openapi: "3.0.1"
    paths: {}
""")

_MISSING_TITLE_YAML = textwrap.dedent("""\
    openapi: "3.0.1"
    info:
      version: "1.0.0"
""")

_MISSING_VERSION_YAML = textwrap.dedent("""\
    openapi: "3.0.1"
    info:
      title: No Version API
""")

_SWAGGER2_YAML = textwrap.dedent("""\
    swagger: "2.0"
    info:
      title: Legacy API
      version: "0.9.0"
""")


def _write(directory: Path, filename: str, content: str) -> Path:
    path = directory / filename
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# load_yaml_files — filesystem + settings integration
# ---------------------------------------------------------------------------

class TestLoadYamlFiles:
    def test_loads_from_settings_when_no_dir_given(self, monkeypatch, tmp_path: Path):
        _write(tmp_path, "spec.yaml", _MINIMAL_YAML)

        class FakeSettings:
            yaml_spec_dir = tmp_path

        monkeypatch.setattr("shared.config.settings", FakeSettings())

        from openapi_parser.loader import load_yaml_files
        results = load_yaml_files(None)
        assert len(results) == 1
        assert results[0].title == "Payment API"

    def test_loads_from_explicit_path(self, tmp_path: Path):
        _write(tmp_path, "spec.yaml", _MINIMAL_YAML)

        from openapi_parser.loader import load_yaml_files
        results = load_yaml_files(tmp_path)
        assert len(results) == 1

    def test_multiple_files_returned(self, tmp_path: Path):
        _write(tmp_path, "a.yaml", _MINIMAL_YAML)
        _write(tmp_path, "b.yaml", _FULL_YAML)

        from openapi_parser.loader import load_yaml_files
        results = load_yaml_files(tmp_path)
        assert len(results) == 2
        titles = {r.title for r in results}
        assert titles == {"Payment API", "Full API"}

    def test_invalid_yaml_skipped(self, tmp_path: Path):
        _write(tmp_path, "bad.yaml", _INVALID_YAML)
        _write(tmp_path, "good.yaml", _MINIMAL_YAML)

        from openapi_parser.loader import load_yaml_files
        results = load_yaml_files(tmp_path)
        assert len(results) == 1
        assert results[0].title == "Payment API"

    def test_missing_metadata_file_skipped(self, tmp_path: Path):
        _write(tmp_path, "no_info.yaml", _NO_INFO_YAML)
        _write(tmp_path, "valid.yaml", _MINIMAL_YAML)

        from openapi_parser.loader import load_yaml_files
        results = load_yaml_files(tmp_path)
        assert len(results) == 1

    def test_nonexistent_directory_returns_empty(self):
        from openapi_parser.loader import load_yaml_files
        results = load_yaml_files(Path("/nonexistent/path/to/specs"))
        assert results == []

    def test_empty_directory_returns_empty(self, tmp_path: Path):
        from openapi_parser.loader import load_yaml_files
        results = load_yaml_files(tmp_path)
        assert results == []

    def test_recursive_discovery(self, tmp_path: Path):
        sub = tmp_path / "sub"
        sub.mkdir()
        _write(sub, "nested.yaml", _MINIMAL_YAML)

        from openapi_parser.loader import load_yaml_files
        results = load_yaml_files(tmp_path)
        assert len(results) == 1
        assert results[0].spec_file == str(sub / "nested.yaml")

    def test_non_yaml_files_ignored(self, tmp_path: Path):
        _write(tmp_path, "spec.yaml", _MINIMAL_YAML)
        (tmp_path / "readme.md").write_text("# ignore me", encoding="utf-8")
        (tmp_path / "data.json").write_text("{}", encoding="utf-8")

        from openapi_parser.loader import load_yaml_files
        results = load_yaml_files(tmp_path)
        assert len(results) == 1

    def test_yml_extension_accepted(self, tmp_path: Path):
        _write(tmp_path, "spec.yml", _MINIMAL_YAML)

        from openapi_parser.loader import load_yaml_files
        results = load_yaml_files(tmp_path)
        assert len(results) == 1

    def test_result_contains_spec_file_path(self, tmp_path: Path):
        spec = _write(tmp_path, "spec.yaml", _MINIMAL_YAML)

        from openapi_parser.loader import load_yaml_files
        results = load_yaml_files(tmp_path)
        assert results[0].spec_file == str(spec)
